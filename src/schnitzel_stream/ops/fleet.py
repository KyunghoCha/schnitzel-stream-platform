from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import shlex
import sys
from typing import Any, Callable


@dataclass(frozen=True)
class StreamSpec:
    stream_id: str
    input_type: str
    input_cfg: dict[str, Any]


_INPUT_PLUGIN_DEFAULTS: dict[str, str] = {
    "rtsp": "schnitzel_stream.packs.vision.nodes:OpenCvRtspSource",
    "file": "schnitzel_stream.packs.vision.nodes:OpenCvVideoFileSource",
    "webcam": "schnitzel_stream.packs.vision.nodes:OpenCvWebcamSource",
}


def as_mapping(raw: Any) -> dict[str, Any]:
    # Intent:
    # - OmegaConf returns DictConfig (Mapping), not a plain dict.
    # - Keep parser robust for both stream(input) and legacy camera(source) keys.
    return dict(raw) if isinstance(raw, Mapping) else {}


def as_list(raw: Any) -> list[Any]:
    if raw is None or isinstance(raw, (str, bytes, Mapping)):
        return []
    try:
        return list(raw)
    except TypeError:
        return []


def load_stream_specs(config_path: Path) -> list[StreamSpec]:
    """Load enabled stream specs from fleet config.

    Supports both:
    - new schema: `streams[].input`
    - legacy schema: `cameras[].source`
    """
    from omegaconf import OmegaConf

    data = OmegaConf.load(config_path)
    raw_streams = as_list(data.get("streams", []))
    if not raw_streams:
        # Intent: one-cycle compatibility bridge for prior camera/source inventory files.
        raw_streams = as_list(data.get("cameras", []))

    specs: list[StreamSpec] = []
    for raw in raw_streams:
        item = as_mapping(raw)
        if not item or not bool(item.get("enabled", True)):
            continue

        stream_id = item.get("id") or item.get("stream_id") or item.get("camera_id")
        if not stream_id:
            continue

        input_cfg = as_mapping(item.get("input"))
        if not input_cfg:
            input_cfg = as_mapping(item.get("source"))

        input_type = str(input_cfg.get("type", "")).strip().lower() or "plugin"
        specs.append(StreamSpec(stream_id=str(stream_id), input_type=input_type, input_cfg=input_cfg))

    return specs


def resolve_stream_subset(specs: list[StreamSpec], raw_streams: str) -> list[StreamSpec]:
    if not raw_streams:
        return specs
    requested = {x.strip() for x in raw_streams.split(",") if x.strip()}
    return [spec for spec in specs if spec.stream_id in requested]


def resolve_input_plugin(spec: StreamSpec) -> str:
    plugin = str(spec.input_cfg.get("plugin", "")).strip()
    if plugin:
        return plugin

    if spec.input_type in _INPUT_PLUGIN_DEFAULTS:
        return _INPUT_PLUGIN_DEFAULTS[spec.input_type]

    raise ValueError(
        f"unsupported input.type={spec.input_type} for stream={spec.stream_id}; "
        "set input.plugin or use one of rtsp/file/webcam/plugin",
    )


def build_stream_env(spec: StreamSpec, *, project_root: Path) -> dict[str, str]:
    plugin = resolve_input_plugin(spec)

    env = {
        "SS_STREAM_ID": spec.stream_id,
        "SS_INPUT_TYPE": spec.input_type,
        "SS_INPUT_PLUGIN": plugin,
        # Intent: keep one-cycle key compatibility for legacy graph templates/scripts.
        "SS_CAMERA_ID": spec.stream_id,
        "SS_SOURCE_TYPE": spec.input_type,
        "SS_SOURCE_PLUGIN": plugin,
    }

    if spec.input_type == "rtsp":
        url = str(spec.input_cfg.get("url", "")).strip()
        if not url:
            raise ValueError(f"stream={spec.stream_id} input.type=rtsp requires input.url")
        env["SS_INPUT_URL"] = url
        env["SS_SOURCE_URL"] = url

    elif spec.input_type == "file":
        path_raw = str(spec.input_cfg.get("path", "")).strip()
        if not path_raw:
            raise ValueError(f"stream={spec.stream_id} input.type=file requires input.path")
        input_path = Path(path_raw)
        if not input_path.is_absolute():
            input_path = (project_root / input_path).resolve()
        env["SS_INPUT_PATH"] = str(input_path)
        env["SS_SOURCE_PATH"] = str(input_path)

    elif spec.input_type == "webcam":
        index = int(spec.input_cfg.get("index", spec.input_cfg.get("camera_index", 0)))
        if index < 0:
            raise ValueError(f"stream={spec.stream_id} webcam index must be >= 0")
        env["SS_INPUT_INDEX"] = str(index)
        env["SS_CAMERA_INDEX"] = str(index)

    elif spec.input_type == "plugin":
        # Intent: keep plugin type open-ended; pass through common keys when present.
        url = str(spec.input_cfg.get("url", "")).strip()
        path_raw = str(spec.input_cfg.get("path", "")).strip()
        index_raw = spec.input_cfg.get("index", spec.input_cfg.get("camera_index", None))

        if url:
            env["SS_INPUT_URL"] = url
            env["SS_SOURCE_URL"] = url
        if path_raw:
            input_path = Path(path_raw)
            if not input_path.is_absolute():
                input_path = (project_root / input_path).resolve()
            env["SS_INPUT_PATH"] = str(input_path)
            env["SS_SOURCE_PATH"] = str(input_path)
        if index_raw is not None:
            index = int(index_raw)
            if index < 0:
                raise ValueError(f"stream={spec.stream_id} input index must be >= 0")
            env["SS_INPUT_INDEX"] = str(index)
            env["SS_CAMERA_INDEX"] = str(index)

    return env


def split_extra_args(raw: str) -> list[str]:
    return shlex.split(raw, posix=not sys.platform.startswith("win")) if raw else []


def start_streams(
    *,
    specs: list[StreamSpec],
    graph_template: Path,
    log_dir: Path,
    project_root: Path,
    extra_args: list[str],
    start_process_fn: Callable[[list[str], Path, Path, dict[str, str]], int],
    is_process_running_fn: Callable[[int], bool],
    python_executable: str,
) -> list[str]:
    pid_dir = log_dir / "pids"
    lines: list[str] = []

    for spec in specs:
        pid_path = pid_dir / f"{spec.stream_id}.pid"
        log_path = log_dir / f"{spec.stream_id}.log"

        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
                if is_process_running_fn(pid):
                    lines.append(f"already running: {spec.stream_id} (pid {pid})")
                    continue
            except (ValueError, IOError):
                pass

        env = {
            "PYTHONPATH": str(project_root / "src"),
            **build_stream_env(spec, project_root=project_root),
        }

        cmd = [
            python_executable,
            "-m",
            "schnitzel_stream",
            "--graph",
            str(graph_template),
            *extra_args,
        ]
        pid = start_process_fn(cmd, log_path, pid_path, env)
        lines.append(f"started {spec.stream_id} pid={pid} input_type={spec.input_type} log={log_path}")

    lines.append("done")
    return lines


def stop_streams(
    *,
    pid_dir: Path,
    stop_process_fn: Callable[[Path], tuple[bool, int | None]],
) -> tuple[int, list[str]]:
    lines: list[str] = []
    stopped = 0
    for pid_file in pid_dir.glob("*.pid"):
        stream_id = pid_file.stem
        success, pid = stop_process_fn(pid_file)
        if success:
            lines.append(f"stopped {stream_id} pid={pid}")
            stopped += 1
        elif pid is not None:
            lines.append(f"stale pid for {stream_id} (pid {pid})")
    lines.append(f"stopped_count={stopped}")
    return stopped, lines


def status_streams(
    *,
    pid_dir: Path,
    is_process_running_fn: Callable[[int], bool],
) -> tuple[int, int, list[str]]:
    lines: list[str] = []
    running = 0
    total = 0
    for pid_file in pid_dir.glob("*.pid"):
        stream_id = pid_file.stem
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except (ValueError, IOError):
            lines.append(f"{stream_id}: invalid pid file")
            total += 1
            continue

        is_running = is_process_running_fn(pid)
        status = "running" if is_running else "stale"
        lines.append(f"{stream_id}: pid={pid} status={status}")
        total += 1
        if is_running:
            running += 1
    lines.append(f"summary: running={running} total={total}")
    return running, total, lines
