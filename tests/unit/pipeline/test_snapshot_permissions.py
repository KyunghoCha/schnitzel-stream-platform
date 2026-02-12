from __future__ import annotations

from pathlib import Path

from ai.events.snapshot import save_snapshot


class _DummyFrame:
    pass


def test_save_snapshot_permission_error(monkeypatch, tmp_path: Path):
    def fake_imwrite(path, frame):
        raise PermissionError("no permission")

    monkeypatch.setattr("ai.events.snapshot.cv2.imwrite", fake_imwrite)

    out = save_snapshot(_DummyFrame(), tmp_path / "x.jpg")
    assert out is None
