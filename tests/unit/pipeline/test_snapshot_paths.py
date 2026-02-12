from __future__ import annotations

from ai.events.snapshot import build_snapshot_path


def test_snapshot_path_sanitizes_timestamp(tmp_path):
    path = build_snapshot_path(
        base_dir=str(tmp_path / "snapshots"),
        site_id="S001",
        camera_id="cam01",
        ts="2026-02-05T12:34:56+09:00",
        track_id=7,
    )
    assert ":" not in path.name
    assert "+" not in path.name
