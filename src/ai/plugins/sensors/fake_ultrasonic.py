from __future__ import annotations

from datetime import datetime, timezone
import os
import threading
from typing import Any


class FakeUltrasonicSensorSource:
    """Deterministic fake ultrasonic sensor source for local tests/demos.

    Plugin path:
        ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource

    Environment variables:
    - AI_FAKE_SENSOR_ID (default: ultrasonic-front-01)
    - AI_FAKE_SENSOR_INTERVAL_SEC (default: 0.05)
    - AI_FAKE_SENSOR_START_CM (default: 120.0)
    - AI_FAKE_SENSOR_STEP_CM (default: 2.0)
    """

    supports_reconnect = True
    base_delay_sec = 0.1
    max_delay_sec = 1.0
    jitter_ratio = 0.1

    def __init__(self) -> None:
        self._sensor_id = os.environ.get("AI_FAKE_SENSOR_ID", "ultrasonic-front-01")
        try:
            self._interval_sec = float(os.environ.get("AI_FAKE_SENSOR_INTERVAL_SEC", "0.05"))
        except ValueError as exc:
            raise RuntimeError("AI_FAKE_SENSOR_INTERVAL_SEC must be a number") from exc
        try:
            self._start_cm = float(os.environ.get("AI_FAKE_SENSOR_START_CM", "120.0"))
        except ValueError as exc:
            raise RuntimeError("AI_FAKE_SENSOR_START_CM must be a number") from exc
        try:
            self._step_cm = float(os.environ.get("AI_FAKE_SENSOR_STEP_CM", "2.0"))
        except ValueError as exc:
            raise RuntimeError("AI_FAKE_SENSOR_STEP_CM must be a number") from exc

        self._value = self._start_cm
        self._stop = threading.Event()
        self._direction = -1.0

    @property
    def sensor_type(self) -> str:
        return "ultrasonic"

    def read(self) -> tuple[bool, Any]:
        if self._stop.wait(max(0.001, self._interval_sec)):
            return False, None
        self._value += self._step_cm * self._direction
        if self._value <= 20.0:
            self._direction = 1.0
        elif self._value >= self._start_cm:
            self._direction = -1.0
        return True, {
            "sensor_id": self._sensor_id,
            "sensor_type": self.sensor_type,
            "sensor_ts": datetime.now(timezone.utc).isoformat(),
            "distance_cm": round(self._value, 2),
            "quality": "ok",
        }

    def release(self) -> None:
        self._stop.set()
