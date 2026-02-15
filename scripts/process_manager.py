# scripts/process_manager.py
# Docs: docs/legacy/ops/multi_camera_run.md
"""
Cross-platform process management utility.
프로세스 시작/중지/PID 관리를 위한 크로스 플랫폼 유틸리티.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def is_windows() -> bool:
    """Windows 환경인지 확인."""
    return sys.platform == "win32"


def is_process_running(pid: int) -> bool:
    """
    주어진 PID의 프로세스가 실행 중인지 확인.
    """
    if is_windows():
        # Windows: use tasklist
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        # Unix: use kill -0
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def start_process(
    cmd: list[str],
    log_path: Path,
    pid_path: Path,
    env: dict | None = None,
) -> int:
    """
    백그라운드 프로세스를 시작하고 PID를 저장.
    
    Args:
        cmd: 실행할 명령어
        log_path: 로그 파일 경로
        pid_path: PID 파일 경로
        env: 환경 변수 (선택)
    
    Returns:
        프로세스 ID
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    with open(log_path, "w", encoding="utf-8") as log_file:
        if is_windows():
            # Windows: use CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=merged_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            # Unix: use start_new_session
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=merged_env,
                start_new_session=True,
            )
    
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid


_SIGTERM_WAIT_SEC = 3.0  # SIGTERM 후 종료 대기 시간


def stop_process(pid_path: Path) -> tuple[bool, int | None]:
    """
    PID 파일을 읽어 프로세스를 종료.
    Unix에서는 SIGTERM → 대기 → SIGKILL 에스컬레이션.

    Returns:
        (성공 여부, PID)
    """
    if not pid_path.exists():
        return False, None

    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (ValueError, IOError):
        pid_path.unlink(missing_ok=True)
        return False, None

    if not is_process_running(pid):
        pid_path.unlink(missing_ok=True)
        return False, pid

    try:
        if is_windows():
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            # SIGTERM → 대기 → SIGKILL 에스컬레이션
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + _SIGTERM_WAIT_SEC
            while time.monotonic() < deadline and is_process_running(pid):
                time.sleep(0.2)
            if is_process_running(pid):
                os.kill(pid, signal.SIGKILL)
        pid_path.unlink(missing_ok=True)
        return True, pid
    except Exception:
        return False, pid


def get_free_port() -> int:
    """
    시스템에서 사용 가능한 포트를 찾아 반환.
    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def is_port_in_use(port: int) -> bool:
    """
    포트가 사용 중인지 확인.
    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
