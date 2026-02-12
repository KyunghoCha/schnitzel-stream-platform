from __future__ import annotations

import importlib
import importlib.util

import pytest


def test_ros2_plugin_modules_are_importable() -> None:
    image_source = importlib.import_module("ai.plugins.ros2.image_source")
    event_emitter = importlib.import_module("ai.plugins.ros2.event_emitter")
    assert image_source is not None
    assert event_emitter is not None


@pytest.mark.skipif(importlib.util.find_spec("rclpy") is not None, reason="rclpy is installed")
def test_ros2_source_plugin_fails_fast_without_ros2() -> None:
    from ai.plugins.ros2.image_source import Ros2ImageSource

    with pytest.raises(RuntimeError, match="rclpy"):
        Ros2ImageSource()


@pytest.mark.skipif(importlib.util.find_spec("rclpy") is not None, reason="rclpy is installed")
def test_ros2_emitter_plugin_fails_fast_without_ros2() -> None:
    from ai.plugins.ros2.event_emitter import Ros2EventEmitter

    with pytest.raises(RuntimeError, match="rclpy"):
        Ros2EventEmitter()
