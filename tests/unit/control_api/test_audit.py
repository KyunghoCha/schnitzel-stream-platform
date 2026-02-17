from __future__ import annotations

from pathlib import Path
import time

from schnitzel_stream.control_api.audit import AuditLogger


def test_audit_append_and_tail(tmp_path: Path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    logger.append(
        actor="local",
        action="fleet.stop",
        target="/tmp/run",
        status="ok",
        reason="ok",
        request_id="r1",
        meta={"k": 1},
    )
    rows = logger.tail(limit=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["actor"] == "local"
    assert row["action"] == "fleet.stop"
    assert row["status"] == "ok"


def test_audit_tail_since_filter(tmp_path: Path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    first = logger.append(
        actor="local",
        action="preset.run",
        target="inproc_demo",
        status="ok",
        reason="ok",
        request_id="r1",
        meta={},
    )
    logger.append(
        actor="local",
        action="preset.run",
        target="inproc_demo",
        status="error",
        reason="runtime_failed",
        request_id="r2",
        meta={},
    )

    rows = logger.tail(limit=10, since=first.ts)
    assert len(rows) == 2


def test_audit_tail_limit(tmp_path: Path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    for idx in range(5):
        logger.append(
            actor="local",
            action="fleet.start",
            target=f"stream{idx}",
            status="ok",
            reason="ok",
            request_id=f"r{idx}",
            meta={},
        )

    rows = logger.tail(limit=2)
    assert len(rows) == 2
    assert rows[0]["target"] == "stream3"
    assert rows[1]["target"] == "stream4"


def test_audit_rotation_respects_max_file_cap(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path, max_bytes=1, max_files=3)
    for idx in range(6):
        logger.append(
            actor="local",
            action="fleet.start",
            target=f"stream{idx}",
            status="ok",
            reason="ok",
            request_id=f"r{idx}",
            meta={},
        )

    assert path.exists()
    assert Path(f"{path}.1").exists()
    assert Path(f"{path}.2").exists()
    assert not Path(f"{path}.3").exists()

    rows = logger.tail(limit=10)
    assert [row["target"] for row in rows] == ["stream3", "stream4", "stream5"]


def test_audit_since_filter_works_across_rotated_files(tmp_path: Path):
    logger = AuditLogger(tmp_path / "audit.jsonl", max_bytes=1, max_files=6)
    logger.append(
        actor="local",
        action="fleet.start",
        target="stream0",
        status="ok",
        reason="ok",
        request_id="r0",
        meta={},
    )
    # Intent: ensure monotonic timestamp ordering so `since=pivot.ts` deterministically excludes r0.
    time.sleep(0.002)
    pivot = logger.append(
        actor="local",
        action="fleet.start",
        target="stream1",
        status="ok",
        reason="ok",
        request_id="r1",
        meta={},
    )
    logger.append(
        actor="local",
        action="fleet.start",
        target="stream2",
        status="ok",
        reason="ok",
        request_id="r2",
        meta={},
    )

    rows = logger.tail(limit=10, since=pivot.ts)
    assert [row["request_id"] for row in rows] == ["r1", "r2"]
