from __future__ import annotations

import sys
import types

import pytest

from ai.plugins.sensors.serial_ultrasonic import _parse_serial_line, SerialUltrasonicSensorSource


def test_parse_serial_line_json() -> None:
    out = _parse_serial_line('{"distance_cm": 12.34, "sensor_id": "u1"}')
    assert out is not None
    assert out["distance_cm"] == 12.34
    assert out["sensor_id"] == "u1"


def test_parse_serial_line_key_value() -> None:
    out = _parse_serial_line("distance_cm=9.8,sensor_id=front-01,sensor_type=ultrasonic")
    assert out is not None
    assert out["distance_cm"] == 9.8
    assert out["sensor_id"] == "front-01"
    assert out["sensor_type"] == "ultrasonic"


def test_parse_serial_line_plain_number() -> None:
    out = _parse_serial_line("15.6")
    assert out == {"distance_cm": 15.6}


def test_parse_serial_line_invalid_returns_none() -> None:
    assert _parse_serial_line("hello world") is None


def test_serial_ultrasonic_requires_port(monkeypatch) -> None:
    fake_serial_module = types.ModuleType("serial")
    fake_serial_module.Serial = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "serial", fake_serial_module)
    monkeypatch.delenv("AI_SERIAL_PORT", raising=False)
    with pytest.raises(RuntimeError, match="AI_SERIAL_PORT is required"):
        SerialUltrasonicSensorSource()


def test_serial_ultrasonic_reads_payload(monkeypatch) -> None:
    class _FakeSerialPort:
        def __init__(self, *args, **kwargs) -> None:
            self._lines = [b'distance_cm=7.5,sensor_id=u-front\n']
            self.closed = False

        def reset_input_buffer(self) -> None:
            return None

        def readline(self) -> bytes:
            if self._lines:
                return self._lines.pop(0)
            return b""

        def close(self) -> None:
            self.closed = True

    fake_serial_module = types.ModuleType("serial")
    fake_serial_module.Serial = _FakeSerialPort  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "serial", fake_serial_module)
    monkeypatch.setenv("AI_SERIAL_PORT", "/dev/ttyACM0")
    monkeypatch.setenv("AI_SENSOR_TYPE", "ultrasonic")

    source = SerialUltrasonicSensorSource()
    ok, payload = source.read()
    source.release()

    assert ok is True
    assert payload["distance_cm"] == 7.5
    assert payload["sensor_id"] == "u-front"
    assert payload["sensor_type"] == "ultrasonic"


def test_serial_ultrasonic_open_error_exposes_root_cause(monkeypatch) -> None:
    class _FailingSerialPort:
        def __init__(self, *args, **kwargs) -> None:
            raise Exception("Device or resource busy")

    fake_serial_module = types.ModuleType("serial")
    fake_serial_module.Serial = _FailingSerialPort  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "serial", fake_serial_module)
    monkeypatch.setenv("AI_SERIAL_PORT", "/dev/ttyACM0")

    with pytest.raises(RuntimeError, match="Device or resource busy"):
        SerialUltrasonicSensorSource()
