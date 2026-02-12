from __future__ import annotations

import time
from typing import Any

from ai.pipeline.processor import FrameProcessor


# -- test helpers -----------------------------------------------------------


class _SingleBuilder:
    """프레임당 이벤트 1개 생성."""

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [{"event_id": f"e{frame_idx}", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"}]


class _MultiBuilder:
    """프레임당 이벤트 2개 생성."""

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [
            {"event_id": f"e{frame_idx}-0", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"},
            {"event_id": f"e{frame_idx}-1", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"},
        ]


class _SlowBuilder:
    """처리에 시간이 걸리는 빌더 (latest-only 테스트용)."""

    def __init__(self, delay: float = 0.1):
        self._delay = delay
        self.processed_indices: list[int] = []

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        time.sleep(self._delay)
        self.processed_indices.append(frame_idx)
        return [{"event_id": f"e{frame_idx}", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"}]


class _CollectEmitter:
    def __init__(self):
        self.payloads: list[dict[str, Any]] = []

    def emit(self, payload: dict[str, Any]) -> bool:
        self.payloads.append(payload)
        return True

    def close(self) -> None:
        pass


class _SlowEmitter:
    """emit에 시간이 걸리는 에미터 (디커플링 테스트용)."""

    def __init__(self, delay: float = 0.5):
        self._delay = delay
        self.payloads: list[dict[str, Any]] = []

    def emit(self, payload: dict[str, Any]) -> bool:
        time.sleep(self._delay)
        self.payloads.append(payload)
        return True

    def close(self) -> None:
        pass


class _FakeZoneEvaluator:
    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload["zone"] = {"zone_id": "z1", "inside": True}
        return payload


class _SlowZoneEvaluator:
    """zone eval에 시간이 걸리는 평가기 (디커플링 테스트용)."""

    def __init__(self, delay: float = 0.5):
        self._delay = delay

    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        time.sleep(self._delay)
        payload["zone"] = {"zone_id": "z1", "inside": True}
        return payload


class _RejectDedup:
    """모든 이벤트를 거부하는 dedup."""

    def allow_emit(self, payload: dict[str, Any]) -> bool:
        return False


class _AllowDedup:
    """모든 이벤트를 허용하는 dedup."""

    def allow_emit(self, payload: dict[str, Any]) -> bool:
        return True


class _NoopMetrics:
    def on_frame(self):
        pass

    def on_event(self):
        pass

    def on_error(self):
        pass

    def on_drop(self):
        pass

    def should_log(self):
        return False

    def snapshot(self):
        return {}


# -- tests ------------------------------------------------------------------


def _wait_for(condition, timeout=5.0, interval=0.02):
    """조건이 True가 될 때까지 대기."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


def test_processor_processes_frame():
    """submit → get_results로 처리 결과를 확인한다."""
    emitter = _CollectEmitter()
    proc = FrameProcessor(event_builder=_SingleBuilder(), emitter=emitter)

    try:
        proc.submit(0, "frame-0")
        assert _wait_for(lambda: len(emitter.payloads) >= 1)

        results = proc.get_results()
        assert len(results) == 1
        assert results[0]["event_id"] == "e0"
    finally:
        proc.stop()


def test_processor_latest_only():
    """빠르게 여러 프레임을 submit하면 마지막만 처리된다."""
    builder = _SlowBuilder(delay=0.15)
    emitter = _CollectEmitter()
    proc = FrameProcessor(event_builder=builder, emitter=emitter)

    try:
        # 빠르게 여러 프레임 제출 — 워커가 바쁜 동안 덮어쓰기
        for i in range(10):
            proc.submit(i, f"frame-{i}")
            time.sleep(0.01)

        # 충분히 대기
        time.sleep(1.0)

        # 모든 프레임이 처리되지는 않음 (latest-only)
        assert len(builder.processed_indices) < 10
        # 최소 1개는 처리됨
        assert len(builder.processed_indices) >= 1
    finally:
        proc.stop()


def test_processor_emitted_count():
    """emitted 카운트가 정확하다."""
    emitter = _CollectEmitter()
    proc = FrameProcessor(event_builder=_MultiBuilder(), emitter=emitter)

    try:
        proc.submit(0, "frame-0")
        assert _wait_for(lambda: proc.emitted >= 2)
        assert proc.emitted == 2

        proc.submit(1, "frame-1")
        assert _wait_for(lambda: proc.emitted >= 4)
        assert proc.emitted == 4
    finally:
        proc.stop()


def test_processor_stop():
    """stop() 후 스레드가 종료된다."""
    emitter = _CollectEmitter()
    proc = FrameProcessor(event_builder=_SingleBuilder(), emitter=emitter)

    assert proc._thread.is_alive()
    proc.stop()
    assert not proc._thread.is_alive()


def test_processor_with_zone_evaluator():
    """zone evaluator가 워커 스레드에서 적용된다."""
    emitter = _CollectEmitter()
    proc = FrameProcessor(
        event_builder=_SingleBuilder(),
        emitter=emitter,
        zone_evaluator=_FakeZoneEvaluator(),
    )

    try:
        proc.submit(0, "frame-0")
        assert _wait_for(lambda: len(emitter.payloads) >= 1)

        assert emitter.payloads[0]["zone"] == {"zone_id": "z1", "inside": True}
    finally:
        proc.stop()


def test_processor_with_dedup():
    """dedup 필터링이 워커 스레드에서 동작한다."""
    emitter = _CollectEmitter()
    proc = FrameProcessor(
        event_builder=_SingleBuilder(),
        emitter=emitter,
        dedup=_RejectDedup(),
    )

    try:
        proc.submit(0, "frame-0")
        # display 결과는 즉시 갱신되어야 함
        assert _wait_for(lambda: len(proc.get_results()) >= 1)

        # 후처리에서 dedup이 거부하므로 emit 없음
        time.sleep(0.3)
        assert len(emitter.payloads) == 0
        assert proc.emitted == 0

        results = proc.get_results()
        # display용 payloads는 생성되지만 emit은 되지 않음
        assert len(results) == 1
    finally:
        proc.stop()


def test_processor_display_not_blocked_by_emit():
    """display 결과가 zone/emit 지연 전에 즉시 갱신된다 (display-first 검증)."""
    emitter = _SlowEmitter(delay=1.0)
    proc = FrameProcessor(
        event_builder=_SingleBuilder(),
        emitter=emitter,
        zone_evaluator=_SlowZoneEvaluator(delay=1.0),
    )

    try:
        t0 = time.monotonic()
        proc.submit(0, "frame-0")

        # display 결과가 추론 직후 즉시 갱신되어야 함 (zone+emit 2초 블로킹 전)
        assert _wait_for(lambda: len(proc.get_results()) >= 1, timeout=2.0)
        display_time = time.monotonic() - t0

        # display 갱신이 0.5초 이내에 완료되어야 함 (zone 1초 + emit 1초 대기 없이)
        assert display_time < 0.5, f"display took {display_time:.2f}s, should be <0.5s"

        # 이 시점에서 emit은 아직 완료되지 않았어야 함
        assert len(emitter.payloads) == 0

        # 충분히 기다리면 emit도 완료
        assert _wait_for(lambda: len(emitter.payloads) >= 1, timeout=5.0)
    finally:
        proc.stop()


