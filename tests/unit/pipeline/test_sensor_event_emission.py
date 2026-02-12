from __future__ import annotations

from datetime import datetime, timezone

from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.sensors.runtime import SensorPacket
from ai.utils.metrics import MetricsTracker


class _StopSource:
    supports_reconnect = False

    @property
    def is_live(self) -> bool:
        return False

    def read(self):
        return False, None

    def release(self) -> None:
        return None

    def fps(self) -> float:
        return 0.0


class _NeverSample:
    def should_sample(self, frame_idx: int) -> bool:
        return False


class _NoopBuilder:
    def build(self, frame_idx: int, frame):
        return []


class _CollectEmitter:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit(self, payload: dict) -> bool:
        self.payloads.append(payload)
        return True

    def close(self) -> None:
        return None


class _StubSensorRuntime:
    def __init__(self) -> None:
        self._drained = False
        self.stopped = False

    def drain_packets(self):
        if self._drained:
            return []
        self._drained = True
        return [
            SensorPacket(
                sensor_id="S-1",
                sensor_type="ultrasonic",
                source_ts=datetime.now(timezone.utc),
                ingest_ts=datetime.now(timezone.utc),
                payload={"sensor_id": "S-1", "distance_cm": 70.0},
            )
        ]

    def last_packet_age_sec(self):
        return 0.1

    def stop(self) -> None:
        self.stopped = True


class _StubSensorEventBuilder:
    def build(self, packets):
        return [
            {
                "event_id": "sensor-evt-1",
                "event_type": "SENSOR_EVENT",
                "sensor": packets[0].to_event_payload(),
            }
        ]


def test_pipeline_emits_independent_sensor_event() -> None:
    emitter = _CollectEmitter()
    sensor_runtime = _StubSensorRuntime()
    metrics = MetricsTracker(interval_sec=9999, fps_window_sec=5)
    ctx = PipelineContext(
        source=_StopSource(),
        sampler=_NeverSample(),
        event_builder=_NoopBuilder(),
        emitter=emitter,
        metrics=metrics,
        sensor_runtime=sensor_runtime,  # type: ignore[arg-type]
        sensor_event_builder=_StubSensorEventBuilder(),  # type: ignore[arg-type]
        sensor_emit_events=True,
    )

    Pipeline(ctx).run(max_events=1)

    assert len(emitter.payloads) == 1
    assert emitter.payloads[0]["event_type"] == "SENSOR_EVENT"
    assert metrics.events == 1
    assert sensor_runtime.stopped is True
