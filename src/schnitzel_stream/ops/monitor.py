from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Callable


@dataclass
class StreamRuntimeState:
    offset: int = 0
    events_total: int = 0
    event_times: deque[float] = field(default_factory=deque)
    last_packet_ts: str = ""
    last_log_monotonic: float | None = None
    last_error_lines: list[str] = field(default_factory=list)


@dataclass
class MonitorState:
    streams: dict[str, StreamRuntimeState] = field(default_factory=dict)


def discover_stream_ids(log_dir: Path) -> list[str]:
    ids: set[str] = set()

    pid_dir = log_dir / "pids"
    if pid_dir.exists():
        ids.update(p.stem for p in pid_dir.glob("*.pid"))

    if log_dir.exists():
        ids.update(p.stem for p in log_dir.glob("*.log"))

    return sorted(x for x in ids if x)


def read_pid(pid_path: Path) -> tuple[int | None, bool]:
    if not pid_path.exists():
        return None, False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        return pid, True
    except (ValueError, IOError):
        return None, True


def read_new_lines(path: Path, state: StreamRuntimeState) -> list[str]:
    if not path.exists():
        return []

    try:
        size = path.stat().st_size
    except OSError:
        return []

    if int(state.offset) > int(size):
        # Intent: log truncation/rotation must not stall incremental parsing.
        state.offset = 0

    with path.open("r", encoding="utf-8", errors="replace") as f:
        f.seek(int(state.offset))
        text = f.read()
        state.offset = int(f.tell())
    return text.splitlines()


def extract_json_payload(line: str) -> dict[str, Any] | None:
    raw = str(line or "").strip()
    if not raw:
        return None
    idx = raw.find("{")
    if idx < 0:
        return None
    candidate = raw[idx:]
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def append_error_tail(state: StreamRuntimeState, line: str, *, tail_lines: int) -> None:
    text = str(line or "").strip()
    if not text:
        return
    state.last_error_lines.append(text)
    if len(state.last_error_lines) > int(tail_lines):
        del state.last_error_lines[:-int(tail_lines)]


def prune_window(state: StreamRuntimeState, *, now_mono: float, window_sec: int) -> None:
    threshold = float(now_mono) - float(window_sec)
    while state.event_times and float(state.event_times[0]) < threshold:
        state.event_times.popleft()


def update_stream_from_lines(
    state: StreamRuntimeState,
    lines: list[str],
    *,
    now_mono: float,
    window_sec: int,
    tail_lines: int,
) -> None:
    for line in lines:
        payload = extract_json_payload(line)
        if payload is None:
            append_error_tail(state, line, tail_lines=tail_lines)
            continue

        state.events_total += 1
        state.event_times.append(float(now_mono))
        state.last_log_monotonic = float(now_mono)

        packet_ts = payload.get("ts")
        if isinstance(packet_ts, str) and packet_ts.strip():
            state.last_packet_ts = packet_ts.strip()

    prune_window(state, now_mono=now_mono, window_sec=window_sec)


def status_for_pid(
    *,
    pid_known: bool,
    pid: int | None,
    is_process_running_fn: Callable[[int], bool],
) -> str:
    if not pid_known:
        return "no_pid"
    if pid is None:
        return "invalid_pid"
    return "running" if is_process_running_fn(int(pid)) else "stale_pid"


def collect_snapshot(
    log_dir: Path,
    state: MonitorState,
    *,
    window_sec: int,
    tail_lines: int,
    is_process_running_fn: Callable[[int], bool],
) -> dict[str, Any]:
    now_mono = time.monotonic()
    rows: list[dict[str, Any]] = []

    for stream_id in discover_stream_ids(log_dir):
        stream_state = state.streams.setdefault(stream_id, StreamRuntimeState())
        pid_path = log_dir / "pids" / f"{stream_id}.pid"
        pid, pid_known = read_pid(pid_path)
        status = status_for_pid(pid_known=pid_known, pid=pid, is_process_running_fn=is_process_running_fn)

        lines = read_new_lines(log_dir / f"{stream_id}.log", stream_state)
        update_stream_from_lines(
            stream_state,
            lines,
            now_mono=now_mono,
            window_sec=window_sec,
            tail_lines=tail_lines,
        )
        prune_window(stream_state, now_mono=now_mono, window_sec=window_sec)

        eps_window = float(len(stream_state.event_times)) / float(window_sec)
        last_log_age = (
            round(float(now_mono) - float(stream_state.last_log_monotonic), 3)
            if stream_state.last_log_monotonic is not None
            else None
        )
        last_error_tail = " | ".join(stream_state.last_error_lines[-int(tail_lines) :])

        rows.append(
            {
                "stream_id": stream_id,
                "pid": pid,
                "status": status,
                "events_total": int(stream_state.events_total),
                "eps_window": round(eps_window, 3),
                "last_packet_ts": stream_state.last_packet_ts,
                "last_log_age_sec": last_log_age,
                "last_error_tail": last_error_tail,
            }
        )

    running_total = sum(1 for row in rows if row.get("status") == "running")
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "log_dir": str(log_dir),
        "streams_total": len(rows),
        "running_total": int(running_total),
        "streams": rows,
    }


def fmt_cell(value: Any, width: int) -> str:
    txt = "-" if value in (None, "") else str(value)
    if len(txt) > int(width):
        if int(width) <= 3:
            return txt[: int(width)]
        return txt[: int(width) - 3] + "..."
    return txt.ljust(int(width))


def render_table(rows: list[dict[str, Any]]) -> list[str]:
    cols = [
        ("stream_id", 18),
        ("pid", 8),
        ("status", 11),
        ("events_total", 12),
        ("eps_window", 10),
        ("last_packet_ts", 28),
        ("last_log_age_sec", 14),
        ("last_error_tail", 44),
    ]

    header = " ".join(fmt_cell(name, width) for name, width in cols)
    separator = " ".join("-" * width for _, width in cols)
    lines = [header, separator]
    for row in rows:
        line = " ".join(fmt_cell(row.get(name), width) for name, width in cols)
        lines.append(line)
    return lines


def render_snapshot(snapshot: dict[str, Any]) -> str:
    lines = [
        "== Stream Monitor ==",
        f"ts={snapshot.get('ts', '')}",
        f"log_dir={snapshot.get('log_dir', '')}",
        f"streams_total={snapshot.get('streams_total', 0)} running_total={snapshot.get('running_total', 0)}",
        "",
    ]
    rows = snapshot.get("streams", [])
    if isinstance(rows, list) and rows:
        lines.extend(render_table([r for r in rows if isinstance(r, dict)]))
    else:
        lines.append("(no stream pid/log entries discovered)")
    return "\n".join(lines)
