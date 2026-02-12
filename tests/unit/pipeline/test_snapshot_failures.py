from __future__ import annotations

from ai.pipeline.events import DummyEventBuilder


def test_snapshot_save_failure_skips_path(monkeypatch, tmp_path):
    def fake_save(frame, path):
        return None

    monkeypatch.setattr("ai.pipeline.events.save_snapshot", fake_save)

    builder = DummyEventBuilder(
        site_id="S001",
        camera_id="cam01",
        timezone="Asia/Seoul",
        snapshot_base_dir=str(tmp_path / "snapshots"),
        snapshot_public_prefix=str(tmp_path / "snapshots"),
    )

    payloads = builder.build(0, frame=None)
    assert len(payloads) == 1
    assert "snapshot_path" not in payloads[0] or payloads[0]["snapshot_path"] is None
