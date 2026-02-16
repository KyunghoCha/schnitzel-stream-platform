from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def is_process_running(pid: int) -> bool:
    if is_windows():
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_process(
    cmd: list[str],
    log_path: Path,
    pid_path: Path,
    env: dict[str, str] | None = None,
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    with open(log_path, "w", encoding="utf-8") as log_file:
        if is_windows():
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=merged_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=merged_env,
                start_new_session=True,
            )

    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid


_SIGTERM_WAIT_SEC = 3.0


def stop_process(pid_path: Path) -> tuple[bool, int | None]:
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
