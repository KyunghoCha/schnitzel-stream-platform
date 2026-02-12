#!/usr/bin/env python3
# scripts/check_rtsp.py
# Docs: docs/implementation/10-rtsp-stability/README.md
"""
RTSP E2E 안정성 테스트 (크로스 플랫폼).
rtsp_e2e_stability.sh를 대체.

사용법:
    python scripts/check_rtsp.py [--strict] [--log-dir ...]

요구사항:
    - ffmpeg 설치 및 PATH 등록 필요
    - mediamtx는 없으면 자동 다운로드
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

# Add project root to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from process_manager import (
    get_free_port,
    is_port_in_use,
    is_process_running,
    is_windows,
    start_process,
    stop_process,
)

# MediaMTX download URLs by platform
MEDIAMTX_VERSION = "v1.16.0"
MEDIAMTX_URLS = {
    "linux_amd64": f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/mediamtx_{MEDIAMTX_VERSION}_linux_amd64.tar.gz",
    "linux_arm64": f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/mediamtx_{MEDIAMTX_VERSION}_linux_arm64.tar.gz",
    "windows_amd64": f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/mediamtx_{MEDIAMTX_VERSION}_windows_amd64.zip",
    "darwin_amd64": f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/mediamtx_{MEDIAMTX_VERSION}_darwin_amd64.tar.gz",
    "darwin_arm64": f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/mediamtx_{MEDIAMTX_VERSION}_darwin_arm64.tar.gz",
}


def _safe_extract_tar(tar: tarfile.TarFile, dest_dir: Path) -> None:
    """Extract tar safely with Python 3.10-compatible fallback.

    Python 3.11+ supports tarfile.extractall(filter="data"), which blocks most
    unsafe members. On 3.10, we manually reject symlink/hardlink/path-traversal
    members before extraction.
    """
    dest_dir = dest_dir.resolve()
    members = tar.getmembers()
    for member in members:
        if member.issym() or member.islnk():
            raise RuntimeError(f"Refusing tar member with link: {member.name}")
        target = (dest_dir / member.name).resolve()
        if not target.is_relative_to(dest_dir):
            raise RuntimeError(f"Unsafe tar member path: {member.name}")

    try:
        tar.extractall(dest_dir, filter="data")
    except TypeError:
        # Python 3.10 fallback: filter parameter is unavailable.
        tar.extractall(dest_dir, members=members)


def get_mediamtx_key() -> str:
    """현재 플랫폼에 맞는 MediaMTX 키 반환."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in {"x86_64", "amd64"}:
        arch = "amd64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64"
    else:
        arch = machine

    if system == "windows":
        # Windows ARM64에서 x64 에뮬레이션 경로를 우선 사용한다.
        # arm64 전용 바이너리 제공 여부가 릴리스마다 달라 안정성을 위해 amd64로 고정.
        return "windows_amd64"
    if system == "darwin":
        return f"darwin_{arch}"
    if system == "linux":
        return f"linux_{arch}"
    raise RuntimeError(f"Unsupported OS for MediaMTX auto setup: system={system} arch={arch}")


def ensure_mediamtx(cache_dir: Path) -> Path:
    """
    MediaMTX가 있는지 확인하고 없으면 다운로드.
    
    Returns:
        실행 파일 경로 반환.
    """
    key = get_mediamtx_key()
    exe_name = "mediamtx.exe" if is_windows() else "mediamtx"
    exe_path = cache_dir / exe_name
    
    if exe_path.exists():
        return exe_path
    
    url = MEDIAMTX_URLS.get(key)
    if not url:
        raise RuntimeError(f"No MediaMTX download available for platform: {key}")
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading MediaMTX from {url}...")
    archive_name = url.split("/")[-1]
    archive_path = cache_dir / archive_name
    
    urlretrieve(url, archive_path)
    
    print(f"Extracting to {cache_dir}...")
    if archive_name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar:
            _safe_extract_tar(tar, cache_dir)
    elif archive_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(cache_dir)
    
    archive_path.unlink()
    
    if not exe_path.exists():
        raise RuntimeError(f"MediaMTX executable not found after extraction: {exe_path}")
    
    # Make executable on Unix
    if not is_windows():
        os.chmod(exe_path, 0o755)
    
    return exe_path


def check_ffmpeg() -> bool:
    """ffmpeg 사용 가능 여부 확인."""
    return shutil.which("ffmpeg") is not None


def count_events(log_dir: Path) -> int:
    """로그에서 이벤트 수 집계."""
    mock_log = log_dir / "mock_backend.log"
    pipe_log = log_dir / "pipeline.log"
    
    if mock_log.exists():
        target = mock_log
        pattern = "event="
    else:
        target = pipe_log
        pattern = "emit_ok=True"
    
    if not target.exists():
        return 0
    
    try:
        text = target.read_text(encoding="utf-8", errors="ignore")
        return text.count(pattern)
    except Exception:
        return 0


def wait_for_count(log_dir: Path, target_count: int, timeout_sec: float = 15.0) -> bool:
    """
    이벤트 수가 목표에 도달할 때까지 대기.
    """
    start = time.monotonic()
    while time.monotonic() - start < timeout_sec:
        if count_events(log_dir) >= target_count:
            return True
        time.sleep(0.5)
    return False


def run_e2e_test(args: argparse.Namespace) -> int:
    """E2E RTSP 안정성 테스트 실행."""
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Check dependencies
    if not check_ffmpeg():
        print("Error: ffmpeg is required but not found in PATH", file=sys.stderr)
        print("  Windows: Download from https://ffmpeg.org/download.html", file=sys.stderr)
        print("  Linux: sudo apt install ffmpeg", file=sys.stderr)
        return 1
    
    # Setup paths
    video_path = PROJECT_ROOT / "tests" / "play" / "2048246-hd_1920_1080_24fps.mp4"
    if not video_path.exists():
        # Try to find any mp4 in data/samples
        sample_dir = PROJECT_ROOT / "data" / "samples"
        mp4s = list(sample_dir.glob("*.mp4"))
        if not mp4s:
            print(f"Error: No test video found at {video_path} or in {sample_dir}", file=sys.stderr)
            return 1
        video_path = mp4s[0]
    
    cache_dir = Path.home() / ".cache" / "mediamtx" if not is_windows() else Path.home() / "AppData" / "Local" / "mediamtx"
    
    # Get MediaMTX
    try:
        mediamtx_exe = ensure_mediamtx(cache_dir)
    except Exception as e:
        print(f"Error: Failed to setup MediaMTX: {e}", file=sys.stderr)
        return 1
    
    rtsp_url = os.environ.get("RTSP_TEST_URL", "rtsp://127.0.0.1:8554/stream1")
    backend_port = int(os.environ.get("MOCK_BACKEND_PORT", "18080"))
    
    # Check if backend port is in use
    if is_port_in_use(backend_port):
        backend_port = get_free_port()
    
    backend_url = f"http://127.0.0.1:{backend_port}/api/events"
    
    print(f"log_dir={log_dir}")
    print(f"backend_port={backend_port}")
    print(f"video={video_path}")
    
    pids = {}
    
    try:
        # 1. Start MediaMTX
        mt_cfg = log_dir / "mediamtx.yml"
        mt_cfg.write_text("paths:\n  stream1:\n    source: publisher\n", encoding="utf-8")
        
        mt_cmd = [str(mediamtx_exe), str(mt_cfg)]
        mt_pid = start_process(mt_cmd, log_dir / "mediamtx.log", log_dir / "mediamtx.pid")
        pids["mediamtx"] = log_dir / "mediamtx.pid"
        print(f"started mediamtx pid={mt_pid}")
        time.sleep(1)
        
        # 2. Start mock backend
        backend_cmd = [sys.executable, "-m", "ai.pipeline.mock_backend"]
        backend_env = {
            "MOCK_BACKEND_PORT": str(backend_port),
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
        }
        backend_pid = start_process(backend_cmd, log_dir / "mock_backend.log", log_dir / "backend.pid", backend_env)
        pids["backend"] = log_dir / "backend.pid"
        print(f"started mock_backend pid={backend_pid}")
        time.sleep(1)
        
        # 3. Start ffmpeg (publish to RTSP)
        ffmpeg_cmd = [
            "ffmpeg", "-re", "-stream_loop", "-1",
            "-i", str(video_path),
            "-an", "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "rtsp", rtsp_url,
        ]
        ffmpeg_pid = start_process(ffmpeg_cmd, log_dir / "ffmpeg.log", log_dir / "ffmpeg.pid")
        pids["ffmpeg"] = log_dir / "ffmpeg.pid"
        print(f"started ffmpeg pid={ffmpeg_pid}")
        time.sleep(3)
        
        # 4. Start pipeline
        pipeline_cmd = [
            sys.executable, "-m", "ai.pipeline",
            "--source-type", "rtsp",
            "--camera-id", "cam01",
        ]
        pipeline_env = {
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            # 의도: RTSP 안정성 검증은 모델 정확도 검증이 아니라 reconnect 동작성 검증이다.
            # 런타임 기본값(real)과 분리해 mock 모드를 명시적으로 사용한다.
            "AI_MODEL_MODE": "mock",
            "AI_EVENTS_POST_URL": backend_url,
            "AI_EVENTS_SNAPSHOT_BASE_DIR": str(log_dir / "snapshots"),
            "AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX": str(log_dir / "snapshots"),
        }
        pipeline_pid = start_process(pipeline_cmd, log_dir / "pipeline.log", log_dir / "pipeline.pid", pipeline_env)
        pids["pipeline"] = log_dir / "pipeline.pid"
        print(f"started pipeline pid={pipeline_pid}")
        
        # 5. Wait for initial events
        print("Waiting for initial events...")
        wait_for_count(log_dir, 1, timeout_sec=30)
        count_before = count_events(log_dir)
        print(f"count_before={count_before}")
        
        # 6. Kill ffmpeg to simulate disconnect
        print("Simulating RTSP disconnect...")
        stop_process(pids["ffmpeg"])
        time.sleep(4)
        
        # 7. Restart ffmpeg
        print("Restarting RTSP stream...")
        ffmpeg_pid = start_process(ffmpeg_cmd, log_dir / "ffmpeg_restart.log", log_dir / "ffmpeg.pid")
        pids["ffmpeg"] = log_dir / "ffmpeg.pid"
        print(f"restarted ffmpeg pid={ffmpeg_pid}")
        
        # 8. Wait for recovery
        print("Waiting for recovery...")
        recovered = wait_for_count(log_dir, count_before + 1, timeout_sec=30)
        count_after = count_events(log_dir)
        
        print(f"count_after={count_after}")
        print(f"recovered={recovered}")
        
        # Write status
        status = f"count_before={count_before}\ncount_after={count_after}\nrecovered={recovered}\nbackend_port={backend_port}\n"
        (log_dir / "status.txt").write_text(status, encoding="utf-8")
        print(f"Logs: {log_dir}")
        
        if args.strict and not recovered:
            print("Error: reconnect not recovered (STRICT=1)", file=sys.stderr)
            return 1
        
        return 0
        
    finally:
        # Cleanup all processes
        for name, pid_path in pids.items():
            success, pid = stop_process(pid_path)
            if success:
                print(f"stopped {name} pid={pid}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RTSP E2E stability test (cross-platform)"
    )
    parser.add_argument(
        "--log-dir", "-l",
        default=str(Path(tempfile.gettempdir()) / "ai_pipeline_e2e_rtsp_stability"),
        help="Directory for logs",
    )
    parser.add_argument(
        "--strict", "-s",
        action="store_true",
        help="Exit with error if recovery fails",
    )
    
    args = parser.parse_args()
    sys.exit(run_e2e_test(args))


if __name__ == "__main__":
    main()
