#!/usr/bin/env python3
# scripts/multi_cam.py
# Docs: docs/legacy/ops/multi_camera_run.md
"""
멀티 카메라 파이프라인 실행기 (크로스 플랫폼).
multi_camera_run.sh 및 multi_camera_stop.sh를 대체.

사용법:
    python scripts/multi_cam.py start [--config ...] [--log-dir ...] [--extra-args ...]
    python scripts/multi_cam.py stop [--log-dir ...]
    python scripts/multi_cam.py status [--log-dir ...]
"""
from __future__ import annotations

import argparse
import shlex
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from process_manager import is_process_running, start_process, stop_process


# Intent: preserve the legacy temp dir name to avoid breaking existing local workflows.
DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "ai_pipeline_multi_cam_run")


def load_camera_ids(config_path: Path) -> list[str]:
    """
    설정 파일에서 활성화된 카메라 ID 목록을 로드.
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
    cameras = data.get("cameras", [])
    ids = []
    for cam in cameras:
        if not cam.get("enabled", True):
            continue
        cam_id = cam.get("id") or cam.get("camera_id")
        if cam_id:
            ids.append(cam_id)
    return ids


def cmd_start(args: argparse.Namespace) -> None:
    """모든 카메라에 대해 파이프라인 프로세스 시작."""
    config_path = Path(args.config)
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"
    
    camera_ids = args.cameras.split(",") if args.cameras else load_camera_ids(config_path)
    if not camera_ids:
        print(f"Error: No enabled cameras found in {config_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"log_dir={log_dir}")
    print(f"pid_dir={pid_dir}")
    print(f"cameras={','.join(camera_ids)}")
    
    # shell-like parsing으로 quoted arg를 보존 (e.g., "--output-jsonl \"C:\\My Logs\\ev.jsonl\"")
    extra_args = shlex.split(args.extra_args, posix=not sys.platform.startswith("win")) if args.extra_args else []
    
    for cam_id in camera_ids:
        pid_path = pid_dir / f"{cam_id}.pid"
        log_path = log_dir / f"{cam_id}.log"
        
        # Check if already running
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
                if is_process_running(pid):
                    print(f"already running: {cam_id} (pid {pid})")
                    continue
            except (ValueError, IOError):
                pass
        
        cmd = [
            sys.executable, "-m", "schnitzel_stream",
            "--camera-id", cam_id,
            *extra_args,
        ]
        
        env = {"PYTHONPATH": str(PROJECT_ROOT / "src")}
        pid = start_process(cmd, log_path, pid_path, env)
        print(f"started {cam_id} pid={pid} log={log_path}")
    
    print("done")


def cmd_stop(args: argparse.Namespace) -> None:
    """모든 파이프라인 프로세스 종료."""
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
    """모든 파이프라인 프로세스 상태 표시."""
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
    parser = argparse.ArgumentParser(
        description="Multi-camera pipeline launcher (cross-platform)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # start command
    start_parser = subparsers.add_parser("start", help="Start all camera pipelines")
    start_parser.add_argument(
        "--config", "-c",
        default=str(PROJECT_ROOT / "configs" / "cameras.yaml"),
        help="Path to cameras.yaml config file",
    )
    start_parser.add_argument(
        "--log-dir", "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    start_parser.add_argument(
        "--cameras",
        default="",
        help="Comma-separated camera IDs (overrides config)",
    )
    start_parser.add_argument(
        "--extra-args",
        default="",
        help="Extra arguments to pass to pipeline (e.g., '--dry-run')",
    )
    start_parser.set_defaults(func=cmd_start)
    
    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop all camera pipelines")
    stop_parser.add_argument(
        "--log-dir", "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    stop_parser.set_defaults(func=cmd_stop)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show status of all pipelines")
    status_parser.add_argument(
        "--log-dir", "-l",
        default=DEFAULT_LOG_DIR,
        help="Directory for logs and PID files",
    )
    status_parser.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
