"""Sensor plugin templates for multimodal sensor lane."""

from __future__ import annotations

from ai.plugins.sensors.fake_ultrasonic import FakeUltrasonicSensorSource
from ai.plugins.sensors.serial_ultrasonic import SerialUltrasonicSensorSource

__all__ = [
    "FakeUltrasonicSensorSource",
    "SerialUltrasonicSensorSource",
]
