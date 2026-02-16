#!/usr/bin/env python3
# scripts/multi_cam.py
# Docs: docs/ops/command_reference.md
"""
멀티 카메라 파이프라인 실행기 (크로스 플랫폼).
카메라별 v2 그래프 프로세스를 시작/중지/조회한다.

사용법:
    python scripts/multi_cam.py start [--config ...] [--graph-template ...] [--log-dir ...] [--extra-args ...]
    python scripts/multi_cam.py stop [--log-dir ...]
    python scripts/multi_cam.py status [--log-dir ...]
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


# Intent: keep the existing temp dir path so local operational scripts do not break.
DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "ai_pipeline_multi_cam_run")
DEFAULT_GRAPH_TEMPLATE = str(PROJECT_ROOT / "configs" / "graphs" / "dev_camera_template_v2.yaml")


@dataclass(frozen=True)
class CameraSpec:
    camera_id: str
    source_type: str
    source: dict[str, Any]


_SOURCE_PLUGIN_DEFAULTS: dict[str, str] = {
    "rtsp": "schnitzel_stream.packs.vision.nodes:OpenCvRtspSource",
    "file": "schnitzel_stream.packs.vision.nodes:OpenCvVideoFileSource",
    "webcam": "schnitzel_stream.packs.vision.nodes:OpenCvWebcamSource",
}


def _as_mapping(raw: Any) -> dict[str, Any]:
    # Intent:
    # - OmegaConf returns DictConfig (Mapping) instead of plain dict.
    # - Accept generic mappings so source.type/url/path/index are preserved.
    return dict(raw) if isinstance(raw, Mapping) else {}


def load_camera_specs(config_path: Path) -> list[CameraSpec]:
    """설정 파일에서 활성 카메라 스펙을 로드한다."""
    try:
        from omegaconf import OmegaConf
    except ImportError:
        print("Error: omegaconf is required. Run: pip install omegaconf", file=sys.stderr)
        sys.exit(1)

    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    data = OmegaConf.load(config_path)
    cameras = data.get("cameras", [])
    specs: list[CameraSpec] = []

    for cam in cameras:
        if not cam.get("enabled", True):
            continue
        camera_id = cam.get("id") or cam.get("camera_id")
        if not camera_id:
            continue

        source = _as_mapping(cam.get("source", {}))
        source_type = str(source.get("type", "")).strip().lower() or "plugin"
        specs.append(CameraSpec(camera_id=str(camera_id), source_type=source_type, source=source))

    return specs


def _resolve_camera_subset(specs: list[CameraSpec], raw_cameras: str) -> list[CameraSpec]:
    if not raw_cameras:
        return specs

    requested = {x.strip() for x in raw_cameras.split(",") if x.strip()}
    return [spec for spec in specs if spec.camera_id in requested]


def _resolve_source_plugin(spec: CameraSpec) -> str:
    plugin = str(spec.source.get("plugin", "")).strip()
    if plugin:
        return plugin

    if spec.source_type in _SOURCE_PLUGIN_DEFAULTS:
        return _SOURCE_PLUGIN_DEFAULTS[spec.source_type]

    raise ValueError(
        f"unsupported source.type={spec.source_type} for camera={spec.camera_id}; "
        "set source.plugin or use one of rtsp/file/webcam/plugin",
    )


def _camera_env(spec: CameraSpec) -> dict[str, str]:
    plugin = _resolve_source_plugin(spec)

    env = {
        "SS_CAMERA_ID": spec.camera_id,
        "SS_SOURCE_TYPE": spec.source_type,
        "SS_SOURCE_PLUGIN": plugin,
    }

    if spec.source_type == "rtsp":
        url = str(spec.source.get("url", "")).strip()
        if not url:
            raise ValueError(f"camera={spec.camera_id} source.type=rtsp requires source.url")
        env["SS_SOURCE_URL"] = url

    elif spec.source_type == "file":
        path_raw = str(spec.source.get("path", "")).strip()
        if not path_raw:
            raise ValueError(f"camera={spec.camera_id} source.type=file requires source.path")
        source_path = Path(path_raw)
        if not source_path.is_absolute():
            source_path = (PROJECT_ROOT / source_path).resolve()
        env["SS_SOURCE_PATH"] = str(source_path)

    elif spec.source_type == "webcam":
        index = int(spec.source.get("index", spec.source.get("camera_index", 0)))
        if index < 0:
            raise ValueError(f"camera={spec.camera_id} webcam index must be >= 0")
        env["SS_CAMERA_INDEX"] = str(index)

    elif spec.source_type == "plugin":
        # Intent: plugin type remains open-ended; pass through common keys if present.
        url = str(spec.source.get("url", "")).strip()
        path_raw = str(spec.source.get("path", "")).strip()
        index_raw = spec.source.get("index", spec.source.get("camera_index", None))
        if url:
            env["SS_SOURCE_URL"] = url
        if path_raw:
            source_path = Path(path_raw)
            if not source_path.is_absolute():
                source_path = (PROJECT_ROOT / source_path).resolve()
            env["SS_SOURCE_PATH"] = str(source_path)
        if index_raw is not None:
            env["SS_CAMERA_INDEX"] = str(int(index_raw))

    return env


def cmd_start(args: argparse.Namespace) -> None:
    """모든 카메라에 대해 그래프 프로세스를 시작한다."""
    config_path = Path(args.config)
    graph_template = Path(args.graph_template)
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not graph_template.exists():
        print(f"Error: graph template not found: {graph_template}", file=sys.stderr)
        sys.exit(1)

    specs = _resolve_camera_subset(load_camera_specs(config_path), args.cameras)
    if not specs:
        print(f"Error: No enabled cameras found in {config_path}", file=sys.stderr)
        sys.exit(1)

    print(f"log_dir={log_dir}")
    print(f"pid_dir={pid_dir}")
    print(f"graph_template={graph_template}")
    print(f"cameras={','.join(spec.camera_id for spec in specs)}")

    # shell-like parsing으로 quoted arg 보존 (e.g., '--max-events 50')
    extra_args = shlex.split(args.extra_args, posix=not sys.platform.startswith("win")) if args.extra_args else []

    for spec in specs:
        pid_path = pid_dir / f"{spec.camera_id}.pid"
        log_path = log_dir / f"{spec.camera_id}.log"

        # Check if already running.
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
                if is_process_running(pid):
                    print(f"already running: {spec.camera_id} (pid {pid})")
                    continue
            except (ValueError, IOError):
                pass

        env = {
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            **_camera_env(spec),
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
        print(f"started {spec.camera_id} pid={pid} source_type={spec.source_type} log={log_path}")

    print("done")


def cmd_stop(args: argparse.Namespace) -> None:
    """모든 파이프라인 프로세스를 종료한다."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    stopped = 0
    for pid_file in pid_dir.glob("*.pid"):
        cam_id = pid_file.stem
        success, pid = stop_process(pid_file)
        if success:
            print(f"stopped {cam_id} pid={pid}")
            stopped += 1
        elif pid is not None:
            print(f"stale pid for {cam_id} (pid {pid})")

    print(f"stopped_count={stopped}")


def cmd_status(args: argparse.Namespace) -> None:
    """모든 파이프라인 프로세스 상태를 표시한다."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    running = 0
    for pid_file in pid_dir.glob("*.pid"):
        cam_id = pid_file.stem
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            if is_process_running(pid):
                print(f"running: {cam_id} (pid {pid})")
                running += 1
            else:
                print(f"stopped: {cam_id} (stale pid {pid})")
        except (ValueError, IOError):
            print(f"invalid: {cam_id}")

    print(f"running_count={running}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-camera graph launcher (cross-platform)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start command
    start_parser = subparsers.add_parser("start", help="Start all camera graph processes")
    start_parser.add_argument(
        "--config",
        "-c",
        default=str(PROJECT_ROOT / "configs" / "cameras.yaml"),
        help="Path to cameras.yaml config file",
    )
    start_parser.add_argument(
        "--graph-template",
        default=DEFAULT_GRAPH_TEMPLATE,
        help="Path to v2 graph template used for each camera process",
    )
    start_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    start_parser.add_argument(
        "--cameras",
        default="",
        help="Comma-separated camera IDs (overrides config selection)",
    )
    start_parser.add_argument(
        "--extra-args",
        default="",
        help="Extra arguments passed to runtime (e.g., '--max-events 100')",
    )
    start_parser.set_defaults(func=cmd_start)

    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop all camera graph processes")
    stop_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    stop_parser.set_defaults(func=cmd_stop)

    # status command
    status_parser = subparsers.add_parser("status", help="Show status of all graph processes")
    status_parser.add_argument(
        "--log-dir",
        "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
