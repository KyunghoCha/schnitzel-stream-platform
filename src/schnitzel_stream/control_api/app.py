from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from schnitzel_stream.ops import envcheck as env_ops
from schnitzel_stream.ops import fleet as fleet_ops
from schnitzel_stream.ops import monitor as monitor_ops
from schnitzel_stream.ops import presets as preset_ops
from schnitzel_stream.ops import process_manager as procman
from schnitzel_stream.plugins.registry import PluginPolicy

from .audit import AuditLogger
from .auth import configured_token, request_identity, security_mode
from .models import EnvCheckRequest, FleetStartRequest, FleetStopRequest, PresetRequest


SCHEMA_VERSION = 1
DEFAULT_AUDIT_PATH = Path("outputs/audit/stream_control_audit.jsonl")
DEFAULT_LOG_DIR = Path(tempfile.gettempdir()) / "schnitzel_stream_fleet_run"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _abs_path(repo_root: Path, raw: str) -> Path:
    p = Path(str(raw))
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


def _envelope(
    *,
    request_id: str,
    status: str = "ok",
    data: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": str(status),
        "request_id": str(request_id),
        "ts": _iso_now(),
        "data": dict(data or {}),
        "error": error,
    }


def _cors_origins_from_env() -> list[str]:
    raw = os.environ.get("SS_CONTROL_API_CORS_ORIGINS", "").strip()
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    # Intent: allow the default local Vite dev hosts so browser UI can call local API without manual CORS setup.
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]


def create_app(*, repo_root: Path | None = None, audit_path: Path | None = None) -> FastAPI:
    root = (repo_root or _repo_root()).resolve()
    logger = AuditLogger(_abs_path(root, str(audit_path or DEFAULT_AUDIT_PATH)))
    app = FastAPI(title="schnitzel stream control api", version="1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins_from_env(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/api/v1/health")
    def health(request: Request) -> dict[str, Any]:
        actor, req_id = request_identity(request)
        return _envelope(
            request_id=req_id,
            data={
                "service": "stream_control_api",
                "repo_root": str(root),
                "security_mode": security_mode(),
                "token_required": bool(configured_token()),
                "audit_path": str(logger.path),
                "actor": actor,
            },
        )

    @app.get("/api/v1/presets")
    def list_presets(request: Request, experimental: bool = Query(default=False)) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        table = preset_ops.build_preset_table(root)
        rows = preset_ops.list_presets_rows(table=table, include_experimental=bool(experimental))
        presets = [
            {
                "preset_id": row[0],
                "experimental": row[1] == "yes",
                "graph": row[2],
                "description": row[3],
            }
            for row in rows
        ]
        return _envelope(request_id=req_id, data={"presets": presets, "count": len(presets)})

    def _run_preset(
        *,
        request: Request,
        preset_id: str,
        body: PresetRequest,
        validate_only: bool,
    ) -> dict[str, Any]:
        actor, req_id = request_identity(request)
        action = f"preset.{ 'validate' if validate_only else 'run' }"
        target = str(preset_id)
        try:
            table = preset_ops.build_preset_table(root)
            spec = table.get(str(preset_id))
            if spec is None:
                raise HTTPException(status_code=404, detail=f"unknown preset: {preset_id}")
            if spec.experimental and not bool(body.experimental):
                raise HTTPException(status_code=400, detail=f"preset '{preset_id}' requires experimental=true")
            if not spec.graph.exists():
                raise HTTPException(status_code=404, detail=f"graph not found for preset '{preset_id}': {spec.graph}")
            if body.max_events is not None and int(body.max_events) <= 0:
                raise HTTPException(status_code=400, detail="max_events must be > 0")

            env = preset_ops.build_preset_env(
                repo_root=root,
                spec=spec,
                existing_env=os.environ,
                input_path=str(body.input_path),
                camera_index=int(body.camera_index) if body.camera_index is not None else None,
                device=str(body.device),
                loop=str(body.loop),
            )
            if validate_only:
                cmd = [sys.executable, "-m", "schnitzel_stream", "validate", "--graph", str(spec.graph)]
            else:
                cmd = [sys.executable, "-m", "schnitzel_stream", "--graph", str(spec.graph)]
            if body.max_events is not None:
                cmd.extend(["--max-events", str(int(body.max_events))])

            returncode = preset_ops.run_subprocess(cmd=cmd, cwd=root, env=env)
            run_ok = int(returncode) == 0
            if not validate_only:
                logger.append(
                    actor=actor,
                    action=action,
                    target=target,
                    status="ok" if run_ok else "error",
                    reason="ok" if run_ok else "runtime_failed",
                    request_id=req_id,
                    meta={"returncode": int(returncode), "command": preset_ops.shell_cmd(cmd)},
                )
            return _envelope(
                request_id=req_id,
                status="ok" if run_ok else "error",
                data={
                    "preset_id": spec.preset_id,
                    "validate_only": bool(validate_only),
                    "command": preset_ops.shell_cmd(cmd),
                    "graph": str(spec.graph),
                    "returncode": int(returncode),
                },
                error=None if run_ok else {"kind": "runtime_failed", "reason": "subprocess_nonzero"},
            )
        except HTTPException:
            if not validate_only:
                logger.append(
                    actor=actor,
                    action=action,
                    target=target,
                    status="error",
                    reason="request_invalid",
                    request_id=req_id,
                    meta={},
                )
            raise

    @app.post("/api/v1/presets/{preset_id}/validate")
    def validate_preset(request: Request, preset_id: str, body: PresetRequest) -> dict[str, Any]:
        return _run_preset(request=request, preset_id=preset_id, body=body, validate_only=True)

    @app.post("/api/v1/presets/{preset_id}/run")
    def run_preset(request: Request, preset_id: str, body: PresetRequest) -> dict[str, Any]:
        return _run_preset(request=request, preset_id=preset_id, body=body, validate_only=False)

    @app.post("/api/v1/fleet/start")
    def fleet_start(request: Request, body: FleetStartRequest) -> dict[str, Any]:
        actor, req_id = request_identity(request)
        action = "fleet.start"
        try:
            config_path = _abs_path(root, body.config)
            graph_template = _abs_path(root, body.graph_template)
            log_dir = _abs_path(root, body.log_dir)
            if not config_path.exists():
                raise HTTPException(status_code=404, detail=f"config not found: {config_path}")
            if not graph_template.exists():
                raise HTTPException(status_code=404, detail=f"graph template not found: {graph_template}")

            specs = fleet_ops.resolve_stream_subset(fleet_ops.load_stream_specs(config_path), body.streams)
            if not specs:
                raise HTTPException(status_code=400, detail=f"no enabled streams found in {config_path}")

            lines = fleet_ops.start_streams(
                specs=specs,
                graph_template=graph_template,
                log_dir=log_dir,
                project_root=root,
                extra_args=fleet_ops.split_extra_args(str(body.extra_args)),
                start_process_fn=procman.start_process,
                is_process_running_fn=procman.is_process_running,
                python_executable=sys.executable,
            )
            logger.append(
                actor=actor,
                action=action,
                target=str(log_dir),
                status="ok",
                reason="ok",
                request_id=req_id,
                meta={"streams": [s.stream_id for s in specs], "graph_template": str(graph_template)},
            )
            return _envelope(
                request_id=req_id,
                data={
                    "config": str(config_path),
                    "graph_template": str(graph_template),
                    "log_dir": str(log_dir),
                    "lines": lines,
                },
            )
        except HTTPException:
            logger.append(
                actor=actor,
                action=action,
                target=str(body.log_dir),
                status="error",
                reason="request_invalid",
                request_id=req_id,
                meta={},
            )
            raise

    @app.post("/api/v1/fleet/stop")
    def fleet_stop(request: Request, body: FleetStopRequest) -> dict[str, Any]:
        actor, req_id = request_identity(request)
        action = "fleet.stop"
        log_dir = _abs_path(root, body.log_dir)
        pid_dir = log_dir / "pids"
        if not pid_dir.exists():
            lines = [f"pid_dir not found: {pid_dir}"]
            stopped = 0
        else:
            stopped, lines = fleet_ops.stop_streams(pid_dir=pid_dir, stop_process_fn=procman.stop_process)

        logger.append(
            actor=actor,
            action=action,
            target=str(log_dir),
            status="ok",
            reason="ok",
            request_id=req_id,
            meta={"stopped": int(stopped)},
        )
        return _envelope(
            request_id=req_id,
            data={"log_dir": str(log_dir), "stopped_count": int(stopped), "lines": lines},
        )

    @app.get("/api/v1/fleet/status")
    def fleet_status(request: Request, log_dir: str = Query(default=str(DEFAULT_LOG_DIR))) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        log_dir_path = _abs_path(root, log_dir)
        pid_dir = log_dir_path / "pids"
        if not pid_dir.exists():
            return _envelope(
                request_id=req_id,
                data={"log_dir": str(log_dir_path), "running": 0, "total": 0, "lines": [f"pid_dir not found: {pid_dir}"]},
            )
        running, total, lines = fleet_ops.status_streams(pid_dir=pid_dir, is_process_running_fn=procman.is_process_running)
        return _envelope(
            request_id=req_id,
            data={"log_dir": str(log_dir_path), "running": int(running), "total": int(total), "lines": lines},
        )

    @app.get("/api/v1/monitor/snapshot")
    def monitor_snapshot(
        request: Request,
        log_dir: str = Query(default=str(DEFAULT_LOG_DIR)),
        window_sec: int = Query(default=10, ge=1),
        tail_lines: int = Query(default=2, ge=1),
    ) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        snapshot = monitor_ops.collect_snapshot(
            _abs_path(root, log_dir),
            monitor_ops.MonitorState(),
            window_sec=int(window_sec),
            tail_lines=int(tail_lines),
            is_process_running_fn=procman.is_process_running,
        )
        return _envelope(request_id=req_id, data={"snapshot": snapshot})

    @app.post("/api/v1/env/check")
    def env_check(request: Request, body: EnvCheckRequest) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        checks = env_ops.run_checks(
            profile=str(body.profile),
            model_path=_abs_path(root, body.model_path),
            camera_index=int(body.camera_index),
            probe_webcam=bool(body.probe_webcam),
        )
        payload = env_ops.payload(profile=str(body.profile), strict=bool(body.strict), checks=checks)
        code = env_ops.exit_code(checks, strict=bool(body.strict))
        data = dict(payload)
        data["exit_code"] = int(code)
        return _envelope(
            request_id=req_id,
            status="ok" if int(code) == 0 else "error",
            data=data,
            error=None if int(code) == 0 else {"kind": "env_check_failed", "reason": "required_check_failed"},
        )

    @app.get("/api/v1/governance/policy-snapshot")
    def policy_snapshot(request: Request) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        policy = PluginPolicy.from_env()
        data = {
            "security_mode": security_mode(),
            "token_required": bool(configured_token()),
            "allowed_plugin_prefixes": list(policy.allowed_prefixes),
            "allow_all_plugins": bool(policy.allow_all),
            "audit_path": str(logger.path),
        }
        return _envelope(request_id=req_id, data=data)

    @app.get("/api/v1/governance/audit")
    def audit_tail(
        request: Request,
        limit: int = Query(default=50, ge=1, le=1000),
        since: str = Query(default=""),
    ) -> dict[str, Any]:
        _actor, req_id = request_identity(request)
        events = logger.tail(limit=int(limit), since=str(since))
        return _envelope(
            request_id=req_id,
            data={"audit_path": str(logger.path), "count": len(events), "events": events},
        )

    return app
