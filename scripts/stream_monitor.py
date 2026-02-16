#!/usr/bin/env python3
# scripts/stream_monitor.py
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

# Add script directory for local helper imports.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.ops import monitor as monitor_ops
from process_manager import is_process_running


DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "schnitzel_stream_fleet_run")
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_RUNTIME = 2


StreamRuntimeState = monitor_ops.StreamRuntimeState
MonitorState = monitor_ops.MonitorState


def _discover_stream_ids(log_dir: Path) -> list[str]:
    return monitor_ops.discover_stream_ids(log_dir)


def _read_pid(pid_path: Path) -> tuple[int | None, bool]:
    return monitor_ops.read_pid(pid_path)


def _read_new_lines(path: Path, state: StreamRuntimeState) -> list[str]:
    return monitor_ops.read_new_lines(path, state)


def _extract_json_payload(line: str) -> dict[str, Any] | None:
    return monitor_ops.extract_json_payload(line)


def _append_error_tail(state: StreamRuntimeState, line: str, *, tail_lines: int) -> None:
    monitor_ops.append_error_tail(state, line, tail_lines=tail_lines)


def _prune_window(state: StreamRuntimeState, *, now_mono: float, window_sec: int) -> None:
    monitor_ops.prune_window(state, now_mono=now_mono, window_sec=window_sec)


def _update_stream_from_lines(
    state: StreamRuntimeState,
    lines: list[str],
    *,
    now_mono: float,
    window_sec: int,
    tail_lines: int,
) -> None:
    monitor_ops.update_stream_from_lines(
        state,
        lines,
        now_mono=now_mono,
        window_sec=window_sec,
        tail_lines=tail_lines,
    )


def _status_for_pid(*, pid_known: bool, pid: int | None) -> str:
    return monitor_ops.status_for_pid(
        pid_known=pid_known,
        pid=pid,
        is_process_running_fn=is_process_running,
    )


def _collect_snapshot(log_dir: Path, state: MonitorState, *, window_sec: int, tail_lines: int) -> dict[str, Any]:
    return monitor_ops.collect_snapshot(
        log_dir,
        state,
        window_sec=window_sec,
        tail_lines=tail_lines,
        is_process_running_fn=is_process_running,
    )


def _fmt_cell(value: Any, width: int) -> str:
    return monitor_ops.fmt_cell(value, width)


def _render_table(rows: list[dict[str, Any]]) -> list[str]:
    return monitor_ops.render_table(rows)


def _render_snapshot(snapshot: dict[str, Any]) -> str:
    return monitor_ops.render_snapshot(snapshot)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only stream fleet monitor (pid/log based)")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR, help="Fleet log directory")
    parser.add_argument("--refresh-sec", type=float, default=1.0, help="Refresh period in seconds")
    parser.add_argument("--window-sec", type=int, default=10, help="EPS calculation window in seconds")
    parser.add_argument("--tail-lines", type=int, default=2, help="Error tail lines per stream")
    parser.add_argument("--once", action="store_true", help="Print one snapshot and exit")
    parser.add_argument("--json", action="store_true", help="Print snapshot as JSON")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear screen between refreshes")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if float(args.refresh_sec) <= 0:
        print("Error: --refresh-sec must be > 0", file=sys.stderr)
        return EXIT_USAGE
    if int(args.window_sec) <= 0:
        print("Error: --window-sec must be > 0", file=sys.stderr)
        return EXIT_USAGE
    if int(args.tail_lines) <= 0:
        print("Error: --tail-lines must be > 0", file=sys.stderr)
        return EXIT_USAGE

    log_dir = Path(str(args.log_dir)).resolve()
    state = MonitorState()

    try:
        while True:
            snapshot = _collect_snapshot(
                log_dir,
                state,
                window_sec=int(args.window_sec),
                tail_lines=int(args.tail_lines),
            )

            if args.json:
                print(json.dumps(snapshot, separators=(",", ":"), default=str))
            else:
                if not args.once and not args.no_clear:
                    # ANSI clear screen.
                    print("\033[2J\033[H", end="")
                print(_render_snapshot(snapshot))

            if args.once:
                return EXIT_OK
            time.sleep(float(args.refresh_sec))
    except KeyboardInterrupt:
        return EXIT_OK
    except Exception as exc:
        # Intent: monitor failures should be explicit for operators and scripts.
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
