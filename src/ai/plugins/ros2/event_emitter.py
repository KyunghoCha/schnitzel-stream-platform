from __future__ import annotations

import json
import os
from typing import Any


class Ros2EventEmitter:
    """Publish pipeline events to a ROS2 topic as JSON string messages.

    Plugin path example:
        ai.plugins.ros2.event_emitter:Ros2EventEmitter
    """

    def __init__(self) -> None:
        try:
            import rclpy
            from rclpy.node import Node
            from std_msgs.msg import String
        except ImportError as exc:
            raise RuntimeError(
                "Ros2EventEmitter requires ROS2 Python packages (rclpy, std_msgs). "
                "Install ROS2 and source its environment before using this plugin.",
            ) from exc

        self._rclpy = rclpy
        self._String = String

        qos_text = os.environ.get("AI_ROS2_EMITTER_QOS_DEPTH", "100")
        try:
            qos_depth = int(qos_text)
        except ValueError as exc:
            raise RuntimeError("AI_ROS2_EMITTER_QOS_DEPTH must be an integer") from exc

        self._owns_context = False
        if not rclpy.ok():
            rclpy.init(args=None)
            self._owns_context = True

        node_name = os.environ.get("AI_ROS2_EMITTER_NODE_NAME", "ai_event_emitter")
        topic = os.environ.get("AI_ROS2_EVENT_TOPIC", "/ai/events")

        self._node = Node(node_name)
        self._publisher = self._node.create_publisher(String, topic, qos_depth)

    def emit(self, payload: dict[str, Any]) -> bool:
        msg = self._String()
        msg.data = json.dumps(payload, ensure_ascii=False)
        self._publisher.publish(msg)
        return True

    def close(self) -> None:
        if hasattr(self, "_node"):
            self._node.destroy_node()
        if getattr(self, "_owns_context", False) and self._rclpy.ok():
            self._rclpy.shutdown()
