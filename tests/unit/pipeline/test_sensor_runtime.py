from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any

from ai.pipeline.sensors.builder import SensorAwareEventBuilder, SensorEventBuilder
from ai.pipeline.sensors.runtime import MultiSensorRuntime, SensorRuntime


def _wait_for(condition, timeout: float = 3.0, interval: float = 0.01) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


class _QueueSensorSource:
    supports_reconnect = False

    def __init__(self, packets: list[Any]) -> None:
        self._packets = list(packets)
        self.released = False

    @property
    def sensor_type(self) -> str:
        return "ultrasonic"

    def read(self):
        if not self._packets:
            return False, None
        return True, self._packets.pop(0)

    def release(self) -> None:
        self.released = True


def test_sensor_runtime_matches_packet_in_window() -> None:
    now = datetime.now(timezone.utc)
    source = _QueueSensorSource(
        [
            {
                "sensor_id": "S-1",
                "sensor_type": "ultrasonic",
                "sensor_ts": now.isoformat(),
                "distance_cm": 82.4,
            }
        ]
    )
    runtime = SensorRuntime(source, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="front")
    runtime.start()
    try:
        assert _wait_for(lambda: runtime.last_packet_ts() is not None)
        matched = runtime.latest_for_event(now.isoformat(), time_window_ms=500)
        assert matched is not None
        assert matched["sensor_id"] == "S-1"
        assert matched["distance_cm"] == 82.4
        assert matched["sensor_type"] == "ultrasonic"
    finally:
        runtime.stop()
    assert source.released is True


def test_sensor_runtime_returns_none_outside_window() -> None:
    now = datetime.now(timezone.utc)
    old = now - timedelta(seconds=5)
    source = _QueueSensorSource(
        [
            {
                "sensor_id": "S-2",
                "sensor_type": "ultrasonic",
                "sensor_ts": old.isoformat(),
                "distance_cm": 100.0,
            }
        ]
    )
    runtime = SensorRuntime(source, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="front")
    runtime.start()
    try:
        assert _wait_for(lambda: runtime.last_packet_ts() is not None)
        matched = runtime.latest_for_event(now.isoformat(), time_window_ms=100)
        assert matched is None
    finally:
        runtime.stop()


def test_sensor_runtime_drains_packets() -> None:
    now = datetime.now(timezone.utc)
    source = _QueueSensorSource(
        [
            {"sensor_id": "S-3", "sensor_ts": now.isoformat(), "value": 1},
            {"sensor_id": "S-3", "sensor_ts": now.isoformat(), "value": 2},
        ]
    )
    runtime = SensorRuntime(source, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="front")
    runtime.start()
    try:
        assert _wait_for(lambda: len(runtime.drain_packets(limit=1)) == 1)
        remaining = runtime.drain_packets()
        assert len(remaining) <= 1
    finally:
        runtime.stop()


def test_multi_sensor_runtime_selects_nearest_packet_across_runtimes() -> None:
    now = datetime.now(timezone.utc)
    source_a = _QueueSensorSource(
        [
            {
                "sensor_id": "S-A",
                "sensor_type": "ultrasonic",
                "sensor_ts": (now - timedelta(milliseconds=250)).isoformat(),
                "distance_cm": 100.0,
            }
        ]
    )
    source_b = _QueueSensorSource(
        [
            {
                "sensor_id": "S-B",
                "sensor_type": "ultrasonic",
                "sensor_ts": (now - timedelta(milliseconds=20)).isoformat(),
                "distance_cm": 70.0,
            }
        ]
    )
    runtime_a = SensorRuntime(source_a, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="front")
    runtime_b = SensorRuntime(source_b, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="rear")
    runtime = MultiSensorRuntime([runtime_a, runtime_b])
    runtime.start()
    try:
        assert _wait_for(lambda: runtime.last_packet_ts() is not None)
        matched = runtime.latest_for_event(now.isoformat(), time_window_ms=500)
        assert matched is not None
        assert matched["sensor_id"] == "S-B"
        drained = runtime.drain_packets()
        assert len(drained) == 2
    finally:
        runtime.stop()
    assert source_a.released is True
    assert source_b.released is True


class _BaseBuilder:
    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [{"event_id": f"e{frame_idx}", "ts": "2026-02-10T10:00:00+00:00"}]


class _StaticRuntime:
    def latest_for_event(self, event_ts: str | None, time_window_ms: int):
        return {"sensor_id": "STATIC-1", "sensor_ts": "2026-02-10T10:00:00+00:00", "value": 1}


def test_sensor_aware_event_builder_attaches_sensor() -> None:
    builder = SensorAwareEventBuilder(
        base_builder=_BaseBuilder(),
        sensor_runtime=_StaticRuntime(),  # type: ignore[arg-type]
        time_window_ms=300,
    )
    out = builder.build(0, object())
    assert out[0]["sensor"]["sensor_id"] == "STATIC-1"


class _PreFilledBuilder:
    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [{
            "event_id": "e0",
            "ts": "2026-02-10T10:00:00+00:00",
            "sensor": {"sensor_id": "PRESET"},
        }]


def test_sensor_aware_event_builder_keeps_existing_sensor_field() -> None:
    builder = SensorAwareEventBuilder(
        base_builder=_PreFilledBuilder(),
        sensor_runtime=_StaticRuntime(),  # type: ignore[arg-type]
        time_window_ms=300,
    )
    out = builder.build(0, object())
    assert out[0]["sensor"]["sensor_id"] == "PRESET"


def test_sensor_aware_event_builder_emits_fused_event_when_enabled() -> None:
    builder = SensorAwareEventBuilder(
        base_builder=_BaseBuilder(),
        sensor_runtime=_StaticRuntime(),  # type: ignore[arg-type]
        time_window_ms=300,
        emit_fused_events=True,
    )
    out = builder.build(0, object())
    assert len(out) == 2
    assert out[0]["event_id"] == "e0"
    assert out[1]["event_type"] == "FUSED_EVENT"
    assert out[1]["fusion"]["source_event_id"] == "e0"


def test_sensor_event_builder_builds_sensor_event_payload() -> None:
    now = datetime.now(timezone.utc)
    source = _QueueSensorSource([{"sensor_id": "S-7", "sensor_ts": now.isoformat(), "distance_cm": 50.0}])
    runtime = SensorRuntime(source, queue_size=8, sensor_type_hint="ultrasonic", topic_hint="front")
    runtime.start()
    try:
        assert _wait_for(lambda: runtime.last_packet_ts() is not None)
        packets = runtime.drain_packets()
    finally:
        runtime.stop()

    builder = SensorEventBuilder(site_id="S001", camera_id="cam01", timezone="Asia/Seoul")
    payloads = builder.build(packets)
    assert payloads
    payload = payloads[0]
    assert payload["event_type"] == "SENSOR_EVENT"
    assert payload["object_type"] == "SENSOR"
    assert payload["sensor"]["sensor_id"] == "S-7"
