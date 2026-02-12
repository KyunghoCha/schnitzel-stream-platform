from __future__ import annotations

from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.sampler import FrameSampler
from ai.utils.metrics import MetricsTracker


class _DummySource:
    supports_reconnect = True
    base_delay_sec = 0.5
    max_delay_sec = 10.0
    jitter_ratio = 0.2
    camera_id = "cam01"

    @property
    def is_live(self) -> bool:
        return True

    def __init__(self) -> None:
        self._reads = 0
        self._recent_calls = 0
        self.released = False

    def read(self):
        self._reads += 1
        if self._reads == 1:
            return False, None
        return True, object()

    def recent_reconnect(self) -> bool:
        self._recent_calls += 1
        return self._recent_calls == 1

    def release(self) -> None:
        self.released = True

    def fps(self) -> float:
        return 10.0


class _DummyBuilder:
    def build(self, frame_idx: int, frame):
        return [{
            "event_id": "evt-1",
            "ts": "2026-02-05T00:00:00+09:00",
            "site_id": "S001",
            "camera_id": "cam01",
            "event_type": "ZONE_INTRUSION",
            "object_type": "PERSON",
            "severity": "LOW",
            "track_id": 0,
            "bbox": {"x1": 0, "y1": 0, "x2": 1, "y2": 1},
            "confidence": 0.9,
            "zone": {"zone_id": "", "inside": False},
            "snapshot_path": None,
        }]


class _DummyEmitter:
    def __init__(self) -> None:
        self.emitted = 0
        self.closed = False

    def emit(self, payload) -> bool:
        self.emitted += 1
        return True

    def close(self) -> None:
        self.closed = True


def test_recent_reconnect_skips_backoff(monkeypatch) -> None:
    sleeps: list[float] = []

    def fake_sleep(sec: float) -> None:
        sleeps.append(sec)

    monkeypatch.setattr("ai.pipeline.core.time.sleep", fake_sleep)

    src = _DummySource()
    metrics = MetricsTracker(interval_sec=9999, fps_window_sec=5)
    ctx = PipelineContext(
        source=src,
        sampler=FrameSampler(target_fps=10, source_fps=10),
        event_builder=_DummyBuilder(),
        emitter=_DummyEmitter(),
        metrics=metrics,
    )

    Pipeline(ctx).run(max_events=1)

    from ai.pipeline.core import _RECENT_RECONNECT_DELAY
    assert sleeps == [_RECENT_RECONNECT_DELAY]
    assert metrics.errors == 1
    # 비동기 경로(is_live=True)에서는 메인 루프가 processor.emitted를 확인하기 전에
    # 추가 프레임이 처리될 수 있으므로 >= 1로 검증
    assert metrics.events >= 1
    assert src.released is True
