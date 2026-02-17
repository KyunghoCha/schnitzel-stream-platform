from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any, Mapping
from uuid import uuid4

from omegaconf import OmegaConf

from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.graph.validate import validate_graph
from schnitzel_stream.ops import graph_wizard as wizard_ops


DEFAULT_MAX_EVENTS = 30
DEFAULT_TIMEOUT_SEC = 120


class GraphEditorUsageError(ValueError):
    pass


@dataclass(frozen=True)
class GraphValidationResult:
    ok: bool
    error: str
    node_count: int
    edge_count: int


@dataclass(frozen=True)
class GraphRunResult:
    ok: bool
    returncode: int
    command: str
    temp_spec_path: Path | None
    error: str
    stdout_tail: str
    stderr_tail: str


@dataclass(frozen=True)
class GraphProfileRenderResult:
    profile_id: str
    spec: dict[str, Any]
    experimental: bool
    overrides: Mapping[str, str]
    max_events: int | None
    template_path: Path


def _as_mapping(value: Any, *, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GraphEditorUsageError(f"{what} must be a mapping")
    return dict(value)


def _as_list(value: Any, *, what: str) -> list[Any]:
    if not isinstance(value, list):
        raise GraphEditorUsageError(f"{what} must be a list")
    return list(value)


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _opt_text(value: Any) -> str | None:
    txt = _norm_text(value)
    return txt if txt else None


def _tail(text: str, *, lines: int = 20) -> str:
    rows = [row for row in str(text or "").splitlines() if row.strip()]
    if not rows:
        return ""
    return "\n".join(rows[-int(lines) :])


def shell_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in cmd)


def parse_graph_spec_input(spec_input: Mapping[str, Any]) -> tuple[list[NodeSpec], list[EdgeSpec], dict[str, Any]]:
    payload = _as_mapping(spec_input, what="spec")
    version_raw = payload.get("version", 2)
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise GraphEditorUsageError("spec.version must be int") from exc
    if version != 2:
        raise GraphEditorUsageError("spec.version must be 2")

    nodes_raw = _as_list(payload.get("nodes", []), what="spec.nodes")
    edges_raw = _as_list(payload.get("edges", []), what="spec.edges")
    config = payload.get("config", {})
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise GraphEditorUsageError("spec.config must be a mapping")

    nodes: list[NodeSpec] = []
    for idx, item in enumerate(nodes_raw):
        obj = _as_mapping(item, what=f"spec.nodes[{idx}]")
        node_id = _norm_text(obj.get("id", obj.get("node_id")))
        plugin = _norm_text(obj.get("plugin"))
        kind = _norm_text(obj.get("kind") or "node")
        if not node_id:
            raise GraphEditorUsageError(f"spec.nodes[{idx}].id is required")
        if not plugin:
            raise GraphEditorUsageError(f"spec.nodes[{idx}].plugin is required")
        node_cfg = obj.get("config", {})
        if node_cfg is None:
            node_cfg = {}
        if not isinstance(node_cfg, dict):
            raise GraphEditorUsageError(f"spec.nodes[{idx}].config must be a mapping")
        nodes.append(NodeSpec(node_id=node_id, plugin=plugin, kind=kind, config=dict(node_cfg)))

    edges: list[EdgeSpec] = []
    for idx, item in enumerate(edges_raw):
        obj = _as_mapping(item, what=f"spec.edges[{idx}]")
        src = _norm_text(obj.get("src", obj.get("from")))
        dst = _norm_text(obj.get("dst", obj.get("to")))
        if not src or not dst:
            raise GraphEditorUsageError(f"spec.edges[{idx}] requires src/dst")
        edges.append(
            EdgeSpec(
                src=src,
                dst=dst,
                src_port=_opt_text(obj.get("src_port", obj.get("from_port"))),
                dst_port=_opt_text(obj.get("dst_port", obj.get("to_port"))),
            )
        )

    return nodes, edges, dict(config)


def normalized_spec_dict(spec_input: Mapping[str, Any]) -> dict[str, Any]:
    nodes, edges, config = parse_graph_spec_input(spec_input)
    return {
        "version": 2,
        "nodes": [
            {
                "id": node.node_id,
                "kind": node.kind,
                "plugin": node.plugin,
                "config": dict(node.config),
            }
            for node in nodes
        ],
        "edges": [
            {
                "src": edge.src,
                "dst": edge.dst,
                **({"src_port": edge.src_port} if edge.src_port else {}),
                **({"dst_port": edge.dst_port} if edge.dst_port else {}),
            }
            for edge in edges
        ],
        "config": dict(config),
    }


def validate_graph_spec(spec_input: Mapping[str, Any]) -> GraphValidationResult:
    try:
        nodes, edges, _config = parse_graph_spec_input(spec_input)
        validate_graph(nodes, edges, allow_cycles=False)
        validate_graph_compat(nodes, edges, transport="inproc")
        return GraphValidationResult(ok=True, error="", node_count=len(nodes), edge_count=len(edges))
    except Exception as exc:
        return GraphValidationResult(ok=False, error=str(exc), node_count=0, edge_count=0)


def _temp_spec_path(repo_root: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = (repo_root / "outputs" / "tmp" / f"graph_editor_{ts}_{uuid4().hex[:8]}.yaml").resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _write_temp_spec(*, repo_root: Path, spec_input: Mapping[str, Any]) -> Path:
    p = _temp_spec_path(repo_root)
    payload = normalized_spec_dict(spec_input)
    OmegaConf.save(config=OmegaConf.create(payload), f=str(p), resolve=True)
    return p


def run_graph_spec(
    *,
    repo_root: Path,
    spec_input: Mapping[str, Any],
    max_events: int = DEFAULT_MAX_EVENTS,
    python_executable: str | None = None,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> GraphRunResult:
    if int(max_events) <= 0:
        raise GraphEditorUsageError("max_events must be > 0")

    validation = validate_graph_spec(spec_input)
    if not validation.ok:
        return GraphRunResult(
            ok=False,
            returncode=2,
            command="",
            temp_spec_path=None,
            error=validation.error,
            stdout_tail="",
            stderr_tail="",
        )

    spec_path = _write_temp_spec(repo_root=repo_root, spec_input=spec_input)
    py_exec = str(python_executable or os.environ.get("PYTHON", "") or "python")
    cmd = [
        py_exec,
        "-m",
        "schnitzel_stream",
        "--graph",
        str(spec_path),
        "--max-events",
        str(int(max_events)),
    ]
    env = dict(os.environ)
    py_path = str((repo_root / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{existing}" if existing else py_path
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=int(timeout_sec),
        )
    except subprocess.TimeoutExpired as exc:
        return GraphRunResult(
            ok=False,
            returncode=124,
            command=shell_cmd(cmd),
            temp_spec_path=spec_path,
            error=f"graph run timed out after {timeout_sec}s",
            stdout_tail=_tail(str(exc.stdout or "")),
            stderr_tail=_tail(str(exc.stderr or "")),
        )
    return GraphRunResult(
        ok=int(proc.returncode) == 0,
        returncode=int(proc.returncode),
        command=shell_cmd(cmd),
        temp_spec_path=spec_path,
        error="" if int(proc.returncode) == 0 else "subprocess_nonzero",
        stdout_tail=_tail(proc.stdout),
        stderr_tail=_tail(proc.stderr),
    )


def render_profile_spec(
    *,
    repo_root: Path,
    profile_id: str,
    experimental: bool,
    overrides: Mapping[str, Any] | None = None,
) -> GraphProfileRenderResult:
    ov = dict(overrides or {})

    camera_index: int | None
    raw_camera = ov.get("camera_index", None)
    if raw_camera is None or str(raw_camera).strip() == "":
        camera_index = None
    else:
        try:
            camera_index = int(raw_camera)
        except (TypeError, ValueError) as exc:
            raise GraphEditorUsageError("overrides.camera_index must be int") from exc
        if camera_index < 0:
            raise GraphEditorUsageError("overrides.camera_index must be >= 0")

    raw_max_events = ov.get("max_events", None)
    max_events: int | None
    if raw_max_events is None or str(raw_max_events).strip() == "":
        max_events = None
    else:
        try:
            max_events = int(raw_max_events)
        except (TypeError, ValueError) as exc:
            raise GraphEditorUsageError("overrides.max_events must be int") from exc
        if max_events <= 0:
            raise GraphEditorUsageError("overrides.max_events must be > 0")

    table = wizard_ops.load_profile_table(repo_root)
    spec, rendered = wizard_ops.render_profile_spec(
        repo_root=repo_root,
        table=table,
        profile_id=str(profile_id),
        allow_experimental=bool(experimental),
        input_path=str(ov.get("input_path", "") or ""),
        camera_index=camera_index,
        device=str(ov.get("device", "") or ""),
        model_path=str(ov.get("model_path", "") or ""),
        loop=str(ov.get("loop", "") or ""),
        max_events=max_events,
    )
    return GraphProfileRenderResult(
        profile_id=rendered.profile_id,
        spec=spec,
        experimental=rendered.experimental,
        overrides=rendered.overrides,
        max_events=rendered.max_events,
        template_path=rendered.template_path,
    )
