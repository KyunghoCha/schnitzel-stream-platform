from __future__ import annotations

from typing import Any, Callable

from ai.events.schema import build_event_scaffold
from ai.pipeline.events import EventBuilder
from ai.pipeline.sensors.fusion import FusionEngine
from ai.pipeline.sensors.runtime import SensorRuntimeLike, SensorPacket


class SensorEventBuilder:
    """Builds independent sensor events from collected sensor packets."""

    def __init__(self, site_id: str, camera_id: str, timezone: str | None = None) -> None:
        self._site_id = site_id
        self._camera_id = camera_id
        self._timezone = timezone

    def build(self, packets: list[SensorPacket]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for packet in packets:
            payload = build_event_scaffold(
                self._site_id,
                self._camera_id,
                self._timezone,
                ts_override=packet.event_ts.isoformat(),
            )
            payload["event_type"] = "SENSOR_EVENT"
            payload["object_type"] = "SENSOR"
            payload["severity"] = "LOW"
            payload["confidence"] = 1.0
            payload["track_id"] = None
            payload["sensor"] = packet.to_event_payload()
            out.append(payload)
        return out


class SensorAwareEventBuilder:
    """Wraps an EventBuilder and enriches vision events with sensor context."""

    def __init__(
        self,
        base_builder: EventBuilder,
        sensor_runtime: SensorRuntimeLike,
        time_window_ms: int,
        emit_fused_events: bool = False,
        fusion_callback: Callable[[bool], None] | None = None,
    ) -> None:
        self._base_builder = base_builder
        self._fusion_engine = FusionEngine(sensor_runtime, time_window_ms)
        self._emit_fused_events = bool(emit_fused_events)
        self._fusion_callback = fusion_callback

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        payloads = self._base_builder.build(frame_idx, frame)
        out: list[dict[str, Any]] = []
        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            sensor = payload.get("sensor")
            # 의도: 기존 빌더가 명시한 sensor 값이 있으면 덮어쓰지 않는다.
            if sensor is None:
                sensor = self._fusion_engine.nearest_sensor(
                    payload.get("ts"),
                )
                payload["sensor"] = sensor
            out.append(payload)

            if self._fusion_callback is not None:
                self._fusion_callback(sensor is not None)
            if self._emit_fused_events and sensor is not None:
                out.append(self._fusion_engine.build_fused_event(payload, sensor))
        return out
