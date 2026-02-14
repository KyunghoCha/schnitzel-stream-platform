"""ROS2 plugin implementations for pipeline I/O.

- Ros2ImageSource: source plugin (sensor_msgs image topic -> OpenCV frame)
- Ros2EventEmitter: emitter plugin (event payload -> std_msgs/String)
"""

from __future__ import annotations

from ai.plugins.ros2.event_emitter import Ros2EventEmitter
from ai.plugins.ros2.image_source import Ros2ImageSource

__all__ = [
    "Ros2ImageSource",
    "Ros2EventEmitter",
]
