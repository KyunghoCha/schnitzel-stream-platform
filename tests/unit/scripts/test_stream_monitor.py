from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_stream_monitor_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "stream_monitor.py"
    spec = importlib.util.spec_from_file_location("stream_monitor_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _row_by_id(snapshot: dict[str, object], stream_id: str) -> dict[str, object]:
    rows = snapshot.get("streams", [])
    assert isinstance(rows, list)
    for row in rows:
        assert isinstance(row, dict)
        if row.get("stream_id") == stream_id:
            return row
    raise AssertionError(f"stream row not found: {stream_id}")


def test_collect_snapshot_parses_prefixed_json_and_counts(monkeypatch, tmp_path: Path):
    mod = _load_stream_monitor_module()
    log_dir = tmp_path / "run"
    (log_dir / "pids").mkdir(parents=True)
    (log_dir / "pids" / "stream01.pid").write_text("1234", encoding="utf-8")
    (log_dir / "stream01.log").write_text(
        'stream01 {"ts":"2026-02-16T00:00:00Z","kind":"event","source_id":"stream01"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "is_process_running", lambda _pid: True)
    state = mod.MonitorState()
    snapshot = mod._collect_snapshot(log_dir, state, window_sec=10, tail_lines=2)
    row = _row_by_id(snapshot, "stream01")
    assert row["status"] == "running"
    assert row["events_total"] == 1
    assert row["last_packet_ts"] == "2026-02-16T00:00:00Z"
    assert float(row["eps_window"]) > 0.0


def test_collect_snapshot_handles_invalid_and_stale_pid(monkeypatch, tmp_path: Path):
    mod = _load_stream_monitor_module()
    log_dir = tmp_path / "run"
    (log_dir / "pids").mkdir(parents=True)
    (log_dir / "pids" / "stream_bad.pid").write_text("not_a_pid", encoding="utf-8")
    (log_dir / "pids" / "stream_stale.pid").write_text("4321", encoding="utf-8")

    monkeypatch.setattr(mod, "is_process_running", lambda _pid: False)
    state = mod.MonitorState()
    snapshot = mod._collect_snapshot(log_dir, state, window_sec=10, tail_lines=2)
    bad_row = _row_by_id(snapshot, "stream_bad")
    stale_row = _row_by_id(snapshot, "stream_stale")
    assert bad_row["status"] == "invalid_pid"
    assert stale_row["status"] == "stale_pid"


def test_collect_snapshot_ignores_non_json_line_and_keeps_error_tail(monkeypatch, tmp_path: Path):
    mod = _load_stream_monitor_module()
    log_dir = tmp_path / "run"
    log_dir.mkdir(parents=True)
    (log_dir / "stream01.log").write_text("not-json-line\n", encoding="utf-8")

    monkeypatch.setattr(mod, "is_process_running", lambda _pid: False)
    state = mod.MonitorState()
    snapshot = mod._collect_snapshot(log_dir, state, window_sec=10, tail_lines=2)
    row = _row_by_id(snapshot, "stream01")
    assert row["events_total"] == 0
    assert "not-json-line" in str(row["last_error_tail"])


def test_collect_snapshot_recovers_after_log_truncate(monkeypatch, tmp_path: Path):
    mod = _load_stream_monitor_module()
    log_dir = tmp_path / "run"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "stream01.log"

    monkeypatch.setattr(mod, "is_process_running", lambda _pid: False)
    state = mod.MonitorState()

    log_path.write_text('stream01 {"ts":"2026-01-01T00:00:00Z"}\n', encoding="utf-8")
    first = mod._collect_snapshot(log_dir, state, window_sec=10, tail_lines=2)
    first_row = _row_by_id(first, "stream01")
    assert first_row["events_total"] == 1

    # Truncate and append new event line (offset should reset safely).
    log_path.write_text('stream01 {"ts":"2026-01-01T00:00:01Z"}\n', encoding="utf-8")
    second = mod._collect_snapshot(log_dir, state, window_sec=10, tail_lines=2)
    second_row = _row_by_id(second, "stream01")
    assert second_row["events_total"] == 2


def test_run_once_json_outputs_snapshot(monkeypatch, tmp_path: Path, capsys):
    mod = _load_stream_monitor_module()
    log_dir = tmp_path / "run"
    log_dir.mkdir(parents=True)
    (log_dir / "stream01.log").write_text('stream01 {"ts":"2026-01-01T00:00:00Z"}\n', encoding="utf-8")

    monkeypatch.setattr(mod, "is_process_running", lambda _pid: False)
    code = mod.run(["--once", "--json", "--log-dir", str(log_dir)])
    assert code == mod.EXIT_OK

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["streams_total"] == 1


def test_run_usage_error_and_runtime_error_paths(monkeypatch, tmp_path: Path):
    mod = _load_stream_monitor_module()
    assert mod.run(["--once", "--refresh-sec", "0"]) == mod.EXIT_USAGE

    def _boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "_collect_snapshot", _boom)
    code = mod.run(["--once", "--log-dir", str(tmp_path)])
    assert code == mod.EXIT_RUNTIME
