from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
from typing import Any, Callable
from urllib import error as urlerror
from urllib import request as urlrequest


SCHEMA_VERSION = 1
DEFAULT_LOG_DIR = "outputs/console_run"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 18700
DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 5173
DEFAULT_AUDIT_PATH = "outputs/audit/stream_control_audit.jsonl"


StartProcessFn = Callable[[list[str], Path, Path, dict[str, str]], int]
StopProcessFn = Callable[[Path], tuple[bool, int | None]]
IsProcessRunningFn = Callable[[int], bool]


@dataclass(frozen=True)
class ConsolePaths:
    root: Path
    pid_dir: Path
    state_path: Path
    api_pid: Path
    ui_pid: Path
    api_log: Path
    ui_log: Path


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_path(repo_root: Path, raw: str) -> Path:
    p = Path(str(raw))
    if p.is_absolute():
        return p.resolve()
    return (repo_root / p).resolve()


def resolve_console_paths(*, repo_root: Path, log_dir: str = DEFAULT_LOG_DIR) -> ConsolePaths:
    root = _resolve_path(repo_root, log_dir)
    pid_dir = root / "pids"
    return ConsolePaths(
        root=root,
        pid_dir=pid_dir,
        state_path=root / "console_state.json",
        api_pid=pid_dir / "control_api.pid",
        ui_pid=pid_dir / "stream_console_ui.pid",
        api_log=root / "control_api.log",
        ui_log=root / "stream_console_ui.log",
    )


def default_state(
    *,
    paths: ConsolePaths,
    api_host: str = DEFAULT_API_HOST,
    api_port: int = DEFAULT_API_PORT,
    ui_host: str = DEFAULT_UI_HOST,
    ui_port: int = DEFAULT_UI_PORT,
    api_enabled: bool = True,
    ui_enabled: bool = True,
    allow_local_mutations: bool = False,
    token_configured: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ts": _iso_now(),
        "log_dir": str(paths.root),
        "api": {
            "host": str(api_host),
            "port": int(api_port),
            "enabled": bool(api_enabled),
        },
        "ui": {
            "host": str(ui_host),
            "port": int(ui_port),
            "enabled": bool(ui_enabled),
        },
        "allow_local_mutations": bool(allow_local_mutations),
        "token_configured": bool(token_configured),
    }


def load_state(
    paths: ConsolePaths,
    *,
    api_host: str = DEFAULT_API_HOST,
    api_port: int = DEFAULT_API_PORT,
    ui_host: str = DEFAULT_UI_HOST,
    ui_port: int = DEFAULT_UI_PORT,
) -> dict[str, Any]:
    if not paths.state_path.exists():
        return default_state(
            paths=paths,
            api_host=api_host,
            api_port=api_port,
            ui_host=ui_host,
            ui_port=ui_port,
        )
    try:
        payload = json.loads(paths.state_path.read_text(encoding="utf-8"))
    except Exception:
        return default_state(
            paths=paths,
            api_host=api_host,
            api_port=api_port,
            ui_host=ui_host,
            ui_port=ui_port,
        )
    if not isinstance(payload, dict):
        return default_state(
            paths=paths,
            api_host=api_host,
            api_port=api_port,
            ui_host=ui_host,
            ui_port=ui_port,
        )
    return payload


def save_state(paths: ConsolePaths, payload: dict[str, Any]) -> None:
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_pid(pid_path: Path) -> tuple[int | None, bool]:
    if not pid_path.exists():
        return None, False
    try:
        return int(pid_path.read_text(encoding="utf-8").strip()), True
    except Exception:
        return None, True


def pid_status(pid_path: Path, *, is_process_running_fn: IsProcessRunningFn) -> dict[str, Any]:
    pid, pid_known = read_pid(pid_path)
    if not pid_known:
        return {
            "pid_path": str(pid_path),
            "pid_known": False,
            "pid": None,
            "running": False,
            "status": "not_found",
        }
    if pid is None:
        return {
            "pid_path": str(pid_path),
            "pid_known": True,
            "pid": None,
            "running": False,
            "status": "invalid_pid",
        }
    running = bool(is_process_running_fn(int(pid)))
    return {
        "pid_path": str(pid_path),
        "pid_known": True,
        "pid": int(pid),
        "running": running,
        "status": "running" if running else "stale",
    }


def is_port_open(host: str, port: int, *, timeout_sec: float = 0.2) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(float(timeout_sec))
        try:
            sock.connect((str(host), int(port)))
            return True
        except OSError:
            return False


def fetch_api_health(
    *,
    host: str,
    port: int,
    token: str = "",
    timeout_sec: float = 1.0,
) -> dict[str, Any]:
    url = f"http://{host}:{int(port)}/api/v1/health"
    req = urlrequest.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urlrequest.urlopen(req, timeout=float(timeout_sec)) as resp:
            code = int(resp.getcode())
            body_text = resp.read().decode("utf-8", errors="replace")
            payload: dict[str, Any]
            try:
                payload = json.loads(body_text)
            except Exception:
                payload = {"raw": body_text}
            return {
                "ok": 200 <= code < 300,
                "reachable": True,
                "status_code": code,
                "reason": "ok",
                "data": payload,
            }
    except urlerror.HTTPError as exc:
        return {
            "ok": False,
            "reachable": True,
            "status_code": int(exc.code),
            "reason": f"http_error_{int(exc.code)}",
            "data": {},
        }
    except Exception as exc:
        return {
            "ok": False,
            "reachable": False,
            "status_code": None,
            "reason": str(exc),
            "data": {},
        }


def build_api_command(
    *,
    repo_root: Path,
    python_executable: str,
    api_host: str,
    api_port: int,
    audit_path: str = DEFAULT_AUDIT_PATH,
) -> list[str]:
    return [
        str(python_executable),
        str((repo_root / "scripts" / "stream_control_api.py").resolve()),
        "--host",
        str(api_host),
        "--port",
        str(int(api_port)),
        "--audit-path",
        str(_resolve_path(repo_root, audit_path)),
    ]


def build_ui_command(
    *,
    repo_root: Path,
    ui_host: str,
    ui_port: int,
) -> list[str]:
    npm_exec = shutil.which("npm") or "npm"
    # Intent: use npm --prefix so we do not require a per-process cwd in process_manager.start_process.
    return [
        str(npm_exec),
        "--prefix",
        str((repo_root / "apps" / "stream-console").resolve()),
        "run",
        "dev",
        "--",
        "--host",
        str(ui_host),
        "--port",
        str(int(ui_port)),
    ]


def _with_pythonpath(base_env: dict[str, str], *, repo_root: Path) -> dict[str, str]:
    env = dict(base_env)
    py_path = str((repo_root / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{existing}" if existing else py_path
    return env


def build_api_env(
    *,
    repo_root: Path,
    base_env: dict[str, str] | None = None,
    allow_local_mutations: bool = False,
    token: str = "",
) -> dict[str, str]:
    env = _with_pythonpath(dict(base_env or os.environ), repo_root=repo_root)
    if allow_local_mutations:
        env["SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS"] = "true"
    else:
        env.pop("SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS", None)
    if token:
        env["SS_CONTROL_API_TOKEN"] = str(token)
    else:
        env.pop("SS_CONTROL_API_TOKEN", None)
    return env


def build_ui_env(
    *,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    return dict(base_env or os.environ)


def start_service_if_needed(
    *,
    name: str,
    cmd: list[str],
    log_path: Path,
    pid_path: Path,
    env: dict[str, str],
    start_process_fn: StartProcessFn,
    is_process_running_fn: IsProcessRunningFn,
) -> dict[str, Any]:
    status = pid_status(pid_path, is_process_running_fn=is_process_running_fn)
    if bool(status.get("running")):
        return {
            "service": str(name),
            "action": "already_running",
            "pid": status.get("pid"),
            "command": cmd,
            "log_path": str(log_path),
            "pid_path": str(pid_path),
        }
    pid = int(start_process_fn(cmd, log_path, pid_path, env))
    return {
        "service": str(name),
        "action": "started",
        "pid": pid,
        "command": cmd,
        "log_path": str(log_path),
        "pid_path": str(pid_path),
    }


def stop_service_if_present(
    *,
    name: str,
    pid_path: Path,
    stop_process_fn: StopProcessFn,
) -> dict[str, Any]:
    if not pid_path.exists():
        return {
            "service": str(name),
            "action": "not_found",
            "pid": None,
            "pid_path": str(pid_path),
        }
    stopped, pid = stop_process_fn(pid_path)
    return {
        "service": str(name),
        "action": "stopped" if stopped else "stale_or_missing",
        "pid": int(pid) if pid is not None else None,
        "pid_path": str(pid_path),
    }


def _selected_services(*, api_only: bool, ui_only: bool) -> tuple[bool, bool]:
    if bool(api_only) and bool(ui_only):
        raise ValueError("--api-only and --ui-only cannot be used together")
    if bool(api_only):
        return True, False
    if bool(ui_only):
        return False, True
    return True, True


def start_selected_services(
    *,
    repo_root: Path,
    paths: ConsolePaths,
    python_executable: str,
    api_host: str,
    api_port: int,
    ui_host: str,
    ui_port: int,
    allow_local_mutations: bool,
    token: str,
    api_only: bool,
    ui_only: bool,
    start_process_fn: StartProcessFn,
    is_process_running_fn: IsProcessRunningFn,
) -> list[dict[str, Any]]:
    run_api, run_ui = _selected_services(api_only=api_only, ui_only=ui_only)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.pid_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    if run_api:
        api_result = start_service_if_needed(
            name="api",
            cmd=build_api_command(
                repo_root=repo_root,
                python_executable=python_executable,
                api_host=api_host,
                api_port=api_port,
            ),
            log_path=paths.api_log,
            pid_path=paths.api_pid,
            env=build_api_env(
                repo_root=repo_root,
                allow_local_mutations=bool(allow_local_mutations),
                token=str(token),
            ),
            start_process_fn=start_process_fn,
            is_process_running_fn=is_process_running_fn,
        )
        results.append(api_result)

    if run_ui:
        ui_result = start_service_if_needed(
            name="ui",
            cmd=build_ui_command(
                repo_root=repo_root,
                ui_host=ui_host,
                ui_port=ui_port,
            ),
            log_path=paths.ui_log,
            pid_path=paths.ui_pid,
            env=build_ui_env(),
            start_process_fn=start_process_fn,
            is_process_running_fn=is_process_running_fn,
        )
        results.append(ui_result)

    save_state(
        paths,
        default_state(
            paths=paths,
            api_host=api_host,
            api_port=api_port,
            ui_host=ui_host,
            ui_port=ui_port,
            api_enabled=bool(run_api),
            ui_enabled=bool(run_ui),
            allow_local_mutations=bool(allow_local_mutations),
            token_configured=bool(str(token).strip()),
        ),
    )
    return results


def stop_all_services(
    *,
    paths: ConsolePaths,
    stop_process_fn: StopProcessFn,
) -> list[dict[str, Any]]:
    return [
        stop_service_if_present(name="api", pid_path=paths.api_pid, stop_process_fn=stop_process_fn),
        stop_service_if_present(name="ui", pid_path=paths.ui_pid, stop_process_fn=stop_process_fn),
    ]


def collect_status(
    *,
    paths: ConsolePaths,
    is_process_running_fn: IsProcessRunningFn,
    health_token: str = "",
    health_check_fn: Callable[..., dict[str, Any]] = fetch_api_health,
    is_port_open_fn: Callable[[str, int], bool] = is_port_open,
) -> dict[str, Any]:
    state = load_state(paths)
    api_cfg = state.get("api", {}) if isinstance(state.get("api", {}), dict) else {}
    ui_cfg = state.get("ui", {}) if isinstance(state.get("ui", {}), dict) else {}

    api_host = str(api_cfg.get("host", DEFAULT_API_HOST))
    api_port = int(api_cfg.get("port", DEFAULT_API_PORT))
    ui_host = str(ui_cfg.get("host", DEFAULT_UI_HOST))
    ui_port = int(ui_cfg.get("port", DEFAULT_UI_PORT))
    api_enabled = bool(api_cfg.get("enabled", True))
    ui_enabled = bool(ui_cfg.get("enabled", True))

    api_pid = pid_status(paths.api_pid, is_process_running_fn=is_process_running_fn)
    ui_pid = pid_status(paths.ui_pid, is_process_running_fn=is_process_running_fn)

    api_health = (
        health_check_fn(host=api_host, port=api_port, token=str(health_token))
        if bool(api_pid.get("running"))
        else {
            "ok": False,
            "reachable": False,
            "status_code": None,
            "reason": "api_not_running",
            "data": {},
        }
    )
    api_port_open = bool(is_port_open_fn(str(api_host), int(api_port)))
    ui_port_open = bool(is_port_open_fn(str(ui_host), int(ui_port)))

    api_ready = (not api_enabled) or (
        bool(api_pid.get("running"))
        and (
            bool(api_health.get("ok"))
            or int(api_health.get("status_code") or 0) == 401
            or bool(api_health.get("reachable"))
        )
    )
    ui_ready = (not ui_enabled) or (bool(ui_pid.get("running")) and bool(ui_port_open))

    return {
        "schema_version": SCHEMA_VERSION,
        "ts": _iso_now(),
        "log_dir": str(paths.root),
        "ready": bool(api_ready and ui_ready),
        "state": state,
        "api": {
            "host": api_host,
            "port": api_port,
            "enabled": api_enabled,
            "port_open": api_port_open,
            "health": api_health,
            **api_pid,
        },
        "ui": {
            "host": ui_host,
            "port": ui_port,
            "enabled": ui_enabled,
            "port_open": ui_port_open,
            **ui_pid,
        },
    }
