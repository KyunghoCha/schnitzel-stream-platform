from __future__ import annotations

import cv2
import pytest

from ai.pipeline.sources import RtspSource


class _DummyCapture:
    def __init__(self, opened: bool) -> None:
        self._opened = opened
        self.released = False

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        return False, None

    def release(self) -> None:
        self.released = True

    def get(self, _):
        return 0.0


def test_rtsp_max_attempts_sets_fatal(monkeypatch) -> None:
    def fake_vc(*_args):
        return _DummyCapture(opened=False)

    monkeypatch.setattr(cv2, "VideoCapture", fake_vc)
    monkeypatch.setattr("ai.pipeline.sources.rtsp.time.sleep", lambda *_: None)

    with pytest.raises(RuntimeError):
        RtspSource(
            url="rtsp://example/stream",
            max_attempts=2,
            base_delay_sec=0.01,
            max_delay_sec=0.01,
            jitter_ratio=0.0,
        )


def test_rtsp_max_attempts_false_return_sets_fatal(monkeypatch) -> None:
    def fake_vc(*_args):
        return _DummyCapture(opened=False)

    monkeypatch.setattr(cv2, "VideoCapture", fake_vc)
    monkeypatch.setattr("ai.pipeline.sources.rtsp.time.sleep", lambda *_: None)

    monkeypatch.setattr("ai.pipeline.sources.rtsp.RtspSource.__post_init__", lambda self: None)

    src = RtspSource(
        url="rtsp://example/stream",
        max_attempts=1,
        base_delay_sec=0.01,
        max_delay_sec=0.01,
        jitter_ratio=0.0,
    )
    src.cap = None  # type: ignore[assignment]
    ok = src._connect_with_retry(raise_on_fail=False)
    assert ok is False
    assert src.supports_reconnect is False
