from __future__ import annotations

import json
import os
import re
from typing import Any

_FLOAT_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _parse_serial_line(line: str) -> dict[str, Any] | None:
    text = line.strip()
    if not text:
        return None

    # 1) JSON line (recommended)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        distance = _to_float(parsed.get("distance_cm"))
        if distance is None:
            distance = _to_float(parsed.get("distance"))
        if distance is None:
            distance = _to_float(parsed.get("dist_cm"))
        if distance is None:
            return None
        out = dict(parsed)
        out["distance_cm"] = distance
        return out

    # 2) Key-value text (e.g., "distance_cm=12.3,sensor_id=front-01")
    out: dict[str, Any] = {}
    for token in re.split(r"[,\s]+", text):
        if not token:
            continue
        if "=" in token:
            key, value = token.split("=", 1)
        elif ":" in token:
            key, value = token.split(":", 1)
        else:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key in ("distance_cm", "distance", "dist_cm", "dist"):
            distance = _to_float(value)
            if distance is not None:
                out["distance_cm"] = distance
        elif key in ("sensor_id", "id"):
            out["sensor_id"] = value
        elif key in ("sensor_type", "type"):
            out["sensor_type"] = value
    if "distance_cm" in out:
        return out

    # 3) Plain number line (e.g., "12.3")
    m = _FLOAT_RE.search(text)
    if m is None:
        return None
    distance = _to_float(m.group(0))
    if distance is None:
        return None
    return {"distance_cm": distance}


class SerialUltrasonicSensorSource:
    """Read ultrasonic distance values from Arduino serial output.

    Plugin path:
        ai.plugins.sensors.serial_ultrasonic:SerialUltrasonicSensorSource

    Required env:
    - AI_SERIAL_PORT (e.g., /dev/ttyACM0, /dev/ttyUSB0, COM3)

    Optional env:
    - AI_SERIAL_BAUDRATE (default: 115200)
    - AI_SERIAL_READ_TIMEOUT_SEC (default: 0.2)
    - AI_SERIAL_SENSOR_ID (default: ultrasonic-front-01)
    - AI_SENSOR_TYPE (default fallback: ultrasonic)
    """

    supports_reconnect = True
    base_delay_sec = 0.05
    max_delay_sec = 0.5
    jitter_ratio = 0.1

    def __init__(self) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError(
                "SerialUltrasonicSensorSource requires pyserial. Install with: pip install pyserial",
            ) from exc

        port = (os.environ.get("AI_SERIAL_PORT") or "").strip()
        if not port:
            raise RuntimeError("AI_SERIAL_PORT is required for serial ultrasonic sensor plugin")

        baud_text = os.environ.get("AI_SERIAL_BAUDRATE", "115200")
        timeout_text = os.environ.get("AI_SERIAL_READ_TIMEOUT_SEC", "0.2")
        try:
            baudrate = int(baud_text)
        except ValueError as exc:
            raise RuntimeError("AI_SERIAL_BAUDRATE must be an integer") from exc
        try:
            timeout_sec = float(timeout_text)
        except ValueError as exc:
            raise RuntimeError("AI_SERIAL_READ_TIMEOUT_SEC must be a number") from exc

        self._serial_module = serial
        self._sensor_id = os.environ.get("AI_SERIAL_SENSOR_ID", "ultrasonic-front-01")
        sensor_type = (os.environ.get("AI_SENSOR_TYPE") or "").strip()
        self._sensor_type = sensor_type or "ultrasonic"

        try:
            self._ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout_sec)
            if hasattr(self._ser, "reset_input_buffer"):
                self._ser.reset_input_buffer()
        except Exception as exc:
            raise RuntimeError(
                f"failed to open serial port: {port} ({exc}). "
                "Check that Arduino Serial Monitor/Plotter is closed, "
                "the port is correct (ls /dev/ttyACM* /dev/ttyUSB*), "
                "and user permissions include dialout."
            ) from exc

    @property
    def sensor_type(self) -> str:
        return self._sensor_type

    def read(self) -> tuple[bool, Any]:
        try:
            raw = self._ser.readline()
        except Exception as exc:
            raise RuntimeError("serial read failed") from exc

        if not raw:
            return False, None
        line = raw.decode("utf-8", errors="ignore").strip()
        payload = _parse_serial_line(line)
        if payload is None:
            return False, None
        payload.setdefault("sensor_id", self._sensor_id)
        payload.setdefault("sensor_type", self.sensor_type)
        return True, payload

    def release(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass
