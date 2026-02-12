from __future__ import annotations

from typing import Any
from uuid import uuid4

from ai.pipeline.sensors.runtime import SensorRuntimeLike


class FusionEngine:
    """Time-window nearest fusion helper for vision + sensor payloads."""

    def __init__(self, sensor_runtime: SensorRuntimeLike, time_window_ms: int) -> None:
        self._sensor_runtime = sensor_runtime
        self._time_window_ms = int(time_window_ms)

    @property
    def time_window_ms(self) -> int:
        return self._time_window_ms

    def nearest_sensor(self, event_ts: str | None) -> dict[str, Any] | None:
        return self._sensor_runtime.latest_for_event(event_ts, self._time_window_ms)

    def build_fused_event(self, vision_payload: dict[str, Any], sensor: dict[str, Any]) -> dict[str, Any]:
        fused = dict(vision_payload)
        fused["event_id"] = str(uuid4())
        fused["event_type"] = "FUSED_EVENT"
        fused["sensor"] = dict(sensor)
        fused["fusion"] = {
            "source_event_id": vision_payload.get("event_id"),
            "source_event_type": vision_payload.get("event_type"),
            "time_window_ms": self._time_window_ms,
            "strategy": "nearest_by_abs_delta",
        }
        return fused
