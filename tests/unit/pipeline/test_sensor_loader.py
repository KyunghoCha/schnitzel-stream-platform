from __future__ import annotations

import sys
import types

import pytest

from ai.pipeline.sensors import load_sensor_source


def test_load_sensor_source_from_class(monkeypatch):
    module_name = "tests.fake_sensor_module_class"
    module = types.ModuleType(module_name)

    class _Sensor:
        supports_reconnect = True
        sensor_type = "ultrasonic"

        def read(self):
            return False, None

        def release(self):
            return None

    module.CustomSensor = _Sensor
    monkeypatch.setitem(sys.modules, module_name, module)

    sensor = load_sensor_source(f"{module_name}:CustomSensor")
    assert sensor.sensor_type == "ultrasonic"
    sensor.release()


def test_load_sensor_source_rejects_non_sensor(monkeypatch):
    module_name = "tests.fake_sensor_module_bad"
    module = types.ModuleType(module_name)

    class _Bad:
        pass

    module.BadSensor = _Bad
    monkeypatch.setitem(sys.modules, module_name, module)

    with pytest.raises(TypeError, match="not a SensorSource"):
        load_sensor_source(f"{module_name}:BadSensor")
