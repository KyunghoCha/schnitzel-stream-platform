#!/usr/bin/env python3
# scripts/stream_fleet.py
# Docs: docs/ops/command_reference.md
"""
Universal stream fleet launcher (cross-platform).
Start/stop/status management for per-stream v2 graph processes.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import shlex
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add project root to path for imports.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from process_manager import is_process_running, start_process, stop_process


DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "schnitzel_stream_fleet_run")
DEFAULT_GRAPH_TEMPLATE = str(PROJECT_ROOT / "configs" / "graphs" / "dev_stream_template_v2.yaml")
DEFAULT_CONFIG = str(PROJECT_ROOT / "configs" / "fleet.yaml")


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


def _as_mapping(raw: Any) -> dict[str, Any]:
    # Intent:
    # - OmegaConf returns DictConfig (Mapping), not a plain dict.
    # - Keep parser robust for both stream(input) and legacy camera(source) keys.
    return dict(raw) if isinstance(raw, Mapping) else {}


def load_stream_specs(config_path: Path) -> list[StreamSpec]:
    """Load enabled stream specs from fleet config.

    Supports both:
    - new schema: `streams[].input`
    - legacy schema: `cameras[].source`
    """
    try:
        from omegaconf import OmegaConf
    except ImportError:
        print("Error: omegaconf is required. Run: pip install omegaconf", file=sys.stderr)
        sys.exit(1)

    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    data = OmegaConf.load(config_path)
    raw_streams = data.get("streams", [])
    if not isinstance(raw_streams, list):
        raw_streams = []
    if not raw_streams:
        # Intent: one-cycle compatibility bridge for prior camera/source inventory files.
        raw_streams = data.get("cameras", [])
        if not isinstance(raw_streams, list):
            raw_streams = []

    specs: list[StreamSpec] = []
    for raw in raw_streams:
        item = _as_mapping(raw)
        if not item or not bool(item.get("enabled", True)):
            continue

        stream_id = item.get("id") or item.get("stream_id") or item.get("camera_id")
        if not stream_id:
            continue

        input_cfg = _as_mapping(item.get("input"))
        if not input_cfg:
            input_cfg = _as_mapping(item.get("source"))

        input_type = str(input_cfg.get("type", "")).strip().lower() or "plugin"
        specs.append(StreamSpec(stream_id=str(stream_id), input_type=input_type, input_cfg=input_cfg))

    return specs


def _resolve_stream_subset(specs: list[StreamSpec], raw_streams: str) -> list[StreamSpec]:
    if not raw_streams:
        return specs
    requested = {x.strip() for x in raw_streams.split(",") if x.strip()}
    return [spec for spec in specs if spec.stream_id in requested]


def _resolve_input_plugin(spec: StreamSpec) -> str:
    plugin = str(spec.input_cfg.get("plugin", "")).strip()
    if plugin:
        return plugin

    if spec.input_type in _INPUT_PLUGIN_DEFAULTS:
        return _INPUT_PLUGIN_DEFAULTS[spec.input_type]

    raise ValueError(
        f"unsupported input.type={spec.input_type} for stream={spec.stream_id}; "
        "set input.plugin or use one of rtsp/file/webcam/plugin",
    )


def _stream_env(spec: StreamSpec) -> dict[str, str]:
    plugin = _resolve_input_plugin(spec)

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
            input_path = (PROJECT_ROOT / input_path).resolve()
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
                input_path = (PROJECT_ROOT / input_path).resolve()
            env["SS_INPUT_PATH"] = str(input_path)
            env["SS_SOURCE_PATH"] = str(input_path)
        if index_raw is not None:
            index = int(index_raw)
            if index < 0:
                raise ValueError(f"stream={spec.stream_id} input index must be >= 0")
            env["SS_INPUT_INDEX"] = str(index)
            env["SS_CAMERA_INDEX"] = str(index)

    return env


def cmd_start(args: argparse.Namespace) -> None:
    """Start graph processes for all selected streams."""
    config_path = Path(args.config)
    graph_template = Path(args.graph_template)
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not graph_template.exists():
        print(f"Error: graph template not found: {graph_template}", file=sys.stderr)
        sys.exit(1)

    specs = _resolve_stream_subset(load_stream_specs(config_path), args.streams)
    if not specs:
        print(f"Error: No enabled streams found in {config_path}", file=sys.stderr)
        sys.exit(1)

    print(f"log_dir={log_dir}")
    print(f"pid_dir={pid_dir}")
    print(f"graph_template={graph_template}")
    print(f"streams={','.join(spec.stream_id for spec in specs)}")

    extra_args = shlex.split(args.extra_args, posix=not sys.platform.startswith("win")) if args.extra_args else []

    for spec in specs:
        pid_path = pid_dir / f"{spec.stream_id}.pid"
        log_path = log_dir / f"{spec.stream_id}.log"

        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
                if is_process_running(pid):
                    print(f"already running: {spec.stream_id} (pid {pid})")
                    continue
            except (ValueError, IOError):
                pass

        env = {
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            **_stream_env(spec),
        }

        cmd = [
            sys.executable,
            "-m",
            "schnitzel_stream",
            "--graph",
            str(graph_template),
            *extra_args,
        ]

        pid = start_process(cmd, log_path, pid_path, env)
        print(f"started {spec.stream_id} pid={pid} input_type={spec.input_type} log={log_path}")

    print("done")


def cmd_stop(args: argparse.Namespace) -> None:
    """Stop all managed stream processes."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    stopped = 0
    for pid_file in pid_dir.glob("*.pid"):
        stream_id = pid_file.stem
        success, pid = stop_process(pid_file)
        if success:
            print(f"stopped {stream_id} pid={pid}")
            stopped += 1
        elif pid is not None:
            print(f"stale pid for {stream_id} (pid {pid})")

    print(f"stopped_count={stopped}")


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of all managed stream processes."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    running = 0
    for pid_file in pid_dir.glob("*.pid"):
        stream_id = pid_file.stem
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            if is_process_running(pid):
                print(f"running: {stream_id} (pid {pid})")
                running += 1
            else:
                print(f"stopped: {stream_id} (stale pid {pid})")
        except (ValueError, IOError):
            print(f"invalid: {stream_id}")

    print(f"running_count={running}")


def build_parser(*, prog: str = "stream_fleet") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Universal stream fleet launcher (cross-platform)", prog=prog)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start all stream graph processes")
    start_parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG,
        help="Path to fleet config file",
    )
    start_parser.add_argument(
        "--graph-template",
        default=DEFAULT_GRAPH_TEMPLATE,
        help="Path to v2 graph template used for each stream process",
    )
    start_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    start_parser.add_argument(
        "--streams",
        default="",
        help="Comma-separated stream IDs (overrides config selection)",
    )
    start_parser.add_argument(
        "--extra-args",
        default="",
        help="Extra args passed to runtime (for example '--max-events 100')",
    )
    start_parser.set_defaults(func=cmd_start)

    stop_parser = subparsers.add_parser("stop", help="Stop all stream graph processes")
    stop_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    stop_parser.set_defaults(func=cmd_stop)

    status_parser = subparsers.add_parser("status", help="Show status of all stream graph processes")
    status_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    status_parser.set_defaults(func=cmd_status)

    return parser


def run(argv: list[str] | None = None, *, prog: str = "stream_fleet") -> int:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
