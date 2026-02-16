from __future__ import annotations

from pathlib import Path

import pytest

import schnitzel_stream.packs.vision.nodes.video as video_mod
from schnitzel_stream.packs.vision.nodes.video import (
    EveryNthFrameSamplerNode,
    OpenCvRtspSource,
    OpenCvVideoFileSource,
    OpenCvWebcamSource,
)
from schnitzel_stream.packet import StreamPacket


def test_video_file_source_raises_when_missing_file(tmp_path):
    pytest.importorskip("cv2")
    missing = tmp_path / "nope.mp4"
    with pytest.raises(FileNotFoundError):
        OpenCvVideoFileSource(config={"path": str(missing)})


def test_video_file_source_emits_frames_from_sample_mp4():
    pytest.importorskip("cv2")

    root = Path(__file__).resolve().parents[3]
    sample = root / "data" / "samples" / "2048246-hd_1920_1080_24fps.mp4"
    assert sample.exists()

    src = OpenCvVideoFileSource(
        config={
            "path": str(sample),
            "source_id": "cam01",
            "max_frames": 2,
            "start_ts": "2026-02-14T00:00:00Z",
        }
    )
    try:
        out = list(src.run())
        assert len(out) == 2
        assert out[0].kind == "frame"
        assert out[0].source_id == "cam01"
        assert isinstance(out[0].payload, dict)
        assert "frame" in out[0].payload
        assert out[0].payload["frame_idx"] == 0
        assert out[0].meta["idempotency_key"] == "frame:cam01:0"
    finally:
        src.close()


def test_video_file_source_loops_after_eof_when_enabled(monkeypatch, tmp_path: Path):
    sample = tmp_path / "loop.mp4"
    sample.write_bytes(b"not-a-real-video")

    frames = ["f0", "f1"]
    opened = {"count": 0}

    class _FakeCap:
        def __init__(self, *_args, **_kwargs):
            self._opened = True
            self._i = 0
            self.released = False

        def isOpened(self):
            return bool(self._opened)

        def read(self):
            if self._i >= len(frames):
                return False, None
            out = frames[self._i]
            self._i += 1
            return True, out

        def get(self, _prop):
            return float(self._i * 10.0)

        def release(self):
            self.released = True

    class _FakeCv2:
        CAP_PROP_POS_MSEC = 0

        def VideoCapture(self, *_args, **_kwargs):
            opened["count"] += 1
            return _FakeCap()

    monkeypatch.setattr(video_mod, "cv2", _FakeCv2())

    src = OpenCvVideoFileSource(
        config={
            "path": str(sample),
            "source_id": "loop_cam",
            "loop": True,
            "max_frames": 3,
        }
    )
    try:
        out = list(src.run())
        assert len(out) == 3
        assert [p.payload["frame_idx"] for p in out] == [0, 1, 2]
        assert out[0].meta["idempotency_key"] == "frame:loop_cam:0"
        assert out[2].meta["idempotency_key"] == "frame:loop_cam:2"
        # EOF 이후 reopen 되었는지 확인.
        assert opened["count"] >= 2
    finally:
        src.close()


def test_every_nth_sampler_keeps_expected_frames():
    sampler = EveryNthFrameSamplerNode(config={"every_n": 2, "offset": 0})
    pkts = [
        StreamPacket.new(kind="frame", source_id="cam01", payload={"frame": None, "frame_idx": i})
        for i in range(5)
    ]
    kept = []
    for p in pkts:
        kept.extend(list(sampler.process(p)))
    assert [p.payload["frame_idx"] for p in kept] == [0, 2, 4]
    assert sampler.metrics()["kept_total"] == 3
    assert sampler.metrics()["dropped_total"] == 2


def test_rtsp_source_respects_max_attempts(monkeypatch):
    class _FakeCap:
        def __init__(self, *_args, **_kwargs):
            self._opened = False
            self.released = False

        def isOpened(self):
            return bool(self._opened)

        def read(self):
            return False, None

        def release(self):
            self.released = True

    class _FakeCv2:
        def VideoCapture(self, *_args, **_kwargs):
            return _FakeCap()

    monkeypatch.setattr(video_mod, "cv2", _FakeCv2())

    with pytest.raises(RuntimeError):
        OpenCvRtspSource(
            config={
                "url": "rtsp://example.invalid/stream",
                "reconnect": True,
                "reconnect_backoff_sec": 0.0,
                "reconnect_backoff_max_sec": 0.0,
                "reconnect_max_attempts": 2,
            }
        )


def test_rtsp_source_emits_frames_and_stops_at_max_frames(monkeypatch):
    frames = ["f0", "f1"]

    class _FakeCap:
        def __init__(self, *_args, **_kwargs):
            self._opened = True
            self._i = 0
            self.released = False

        def isOpened(self):
            return bool(self._opened)

        def read(self):
            if self._i >= len(frames):
                return False, None
            f = frames[self._i]
            self._i += 1
            return True, f

        def release(self):
            self.released = True

    class _FakeCv2:
        def VideoCapture(self, *_args, **_kwargs):
            return _FakeCap()

    monkeypatch.setattr(video_mod, "cv2", _FakeCv2())

    src = OpenCvRtspSource(
        config={
            "url": "rtsp://example.invalid/stream",
            "source_id": "cam01",
            "max_frames": 2,
            "reconnect": False,
        }
    )
    try:
        out = list(src.run())
        assert len(out) == 2
        assert out[0].kind == "frame"
        assert out[0].meta["epoch"] == 1
        assert out[0].meta["frame_idx"] == 0
        assert out[0].meta["idempotency_key"] == "frame:cam01:1:0"
    finally:
        src.close()


def test_webcam_source_respects_max_attempts(monkeypatch):
    class _FakeCap:
        def __init__(self, *_args, **_kwargs):
            self._opened = False
            self.released = False

        def isOpened(self):
            return bool(self._opened)

        def read(self):
            return False, None

        def release(self):
            self.released = True

    class _FakeCv2:
        def VideoCapture(self, *_args, **_kwargs):
            return _FakeCap()

    monkeypatch.setattr(video_mod, "cv2", _FakeCv2())

    with pytest.raises(RuntimeError):
        OpenCvWebcamSource(
            config={
                "camera_index": 0,
                "reconnect": True,
                "reconnect_backoff_sec": 0.0,
                "reconnect_backoff_max_sec": 0.0,
                "reconnect_max_attempts": 2,
            }
        )


def test_webcam_source_emits_frames_and_stops_at_max_frames(monkeypatch):
    frames = ["f0", "f1"]

    class _FakeCap:
        def __init__(self, *_args, **_kwargs):
            self._opened = True
            self._i = 0
            self.released = False

        def isOpened(self):
            return bool(self._opened)

        def read(self):
            if self._i >= len(frames):
                return False, None
            f = frames[self._i]
            self._i += 1
            return True, f

        def release(self):
            self.released = True

    class _FakeCv2:
        def VideoCapture(self, *_args, **_kwargs):
            return _FakeCap()

    monkeypatch.setattr(video_mod, "cv2", _FakeCv2())

    src = OpenCvWebcamSource(
        config={
            "camera_index": 0,
            "source_id": "webcam01",
            "max_frames": 2,
            "reconnect": False,
        }
    )
    try:
        out = list(src.run())
        assert len(out) == 2
        assert out[0].kind == "frame"
        assert out[0].meta["camera_index"] == 0
        assert out[0].meta["epoch"] == 1
        assert out[0].meta["frame_idx"] == 0
        assert out[0].meta["idempotency_key"] == "frame:webcam01:1:0"
    finally:
        src.close()
