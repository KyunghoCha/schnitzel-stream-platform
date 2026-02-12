from __future__ import annotations

from typing import Any

from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.sampler import FrameSampler


class _FakeSource:
    supports_reconnect = False

    def __init__(self):
        self._count = 0

    @property
    def is_live(self) -> bool:
        return False

    def read(self):
        # emit two frames then stop
        if self._count >= 2:
            return False, None
        self._count += 1
        return True, f"frame-{self._count}"

    def release(self):
        return None

    def fps(self) -> float:
        return 10.0


class _ListBuilder:
    def build(self, frame_idx: int, frame: Any):
        return [
            {"event_id": f"e{frame_idx}-0", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"},
            {"event_id": f"e{frame_idx}-1", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"},
        ]


class _CollectEmitter:
    def __init__(self):
        self.payloads: list[dict[str, Any]] = []

    def emit(self, payload: dict[str, Any]) -> bool:
        self.payloads.append(payload)
        return True

    def close(self) -> None:
        pass


class _NoopMetrics:
    def on_frame(self):
        pass

    def on_event(self):
        pass

    def on_error(self):
        pass

    def should_log(self):
        return False

    def snapshot(self):
        return {}


def test_pipeline_multi_event_builder():
    source = _FakeSource()
    sampler = FrameSampler(target_fps=10, source_fps=10)
    emitter = _CollectEmitter()

    ctx = PipelineContext(
        source=source,
        sampler=sampler,
        event_builder=_ListBuilder(),
        emitter=emitter,
        zone_evaluator=None,
        dedup=None,
        metrics=_NoopMetrics(),
        heartbeat=None,
    )

    Pipeline(ctx).run(max_events=3)

    # max_events는 프레임 처리 완료 후 체크되므로, 프레임0(2개) + 프레임1(2개) = 4개 emit 후 종료
    assert len(emitter.payloads) == 4
    assert emitter.payloads[0]["event_id"] == "e0-0"
    assert emitter.payloads[1]["event_id"] == "e0-1"
    assert emitter.payloads[2]["event_id"] == "e1-0"
    assert emitter.payloads[3]["event_id"] == "e1-1"
