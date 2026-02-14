from __future__ import annotations

import os
import threading
import time
from typing import Any

import cv2
import numpy as np


class Ros2ImageSource:
    """Read frames from a ROS2 image topic.

    Plugin path example:
        ai.plugins.ros2.image_source:Ros2ImageSource

    Environment variables:
    - AI_ROS2_SOURCE_TOPIC (default: /camera/image_raw/compressed)
    - AI_ROS2_SOURCE_MSG_TYPE (compressed | image, default: compressed)
    - AI_ROS2_SOURCE_NODE_NAME (default: ai_frame_source)
    - AI_ROS2_SOURCE_QOS_DEPTH (default: 10)
    - AI_ROS2_SOURCE_READ_TIMEOUT_SEC (default: 1.0)
    - AI_ROS2_SOURCE_FPS_HINT (default: 0)
    """

    supports_reconnect = True

    # Pipeline backoff hints for transient read failures (no frame yet, source hiccup).
    base_delay_sec = 0.1
    max_delay_sec = 1.0
    jitter_ratio = 0.1

    def __init__(self) -> None:
        try:
            import rclpy
            from rclpy.node import Node
            from sensor_msgs.msg import CompressedImage, Image
        except ImportError as exc:
            raise RuntimeError(
                "Ros2ImageSource requires ROS2 Python packages (rclpy, sensor_msgs). "
                "Install ROS2 and source its environment before using this plugin.",
            ) from exc

        self._rclpy = rclpy
        self._CompressedImage = CompressedImage
        self._Image = Image

        qos_text = os.environ.get("AI_ROS2_SOURCE_QOS_DEPTH", "10")
        try:
            qos_depth = int(qos_text)
        except ValueError as exc:
            raise RuntimeError("AI_ROS2_SOURCE_QOS_DEPTH must be an integer") from exc

        timeout_text = os.environ.get("AI_ROS2_SOURCE_READ_TIMEOUT_SEC", "1.0")
        try:
            self._read_timeout_sec = float(timeout_text)
        except ValueError as exc:
            raise RuntimeError("AI_ROS2_SOURCE_READ_TIMEOUT_SEC must be a number") from exc

        fps_text = os.environ.get("AI_ROS2_SOURCE_FPS_HINT", "0")
        try:
            self._fps_hint = float(fps_text)
        except ValueError as exc:
            raise RuntimeError("AI_ROS2_SOURCE_FPS_HINT must be a number") from exc

        self._owns_context = False
        if not rclpy.ok():
            rclpy.init(args=None)
            self._owns_context = True

        node_name = os.environ.get("AI_ROS2_SOURCE_NODE_NAME", "ai_frame_source")
        topic = os.environ.get("AI_ROS2_SOURCE_TOPIC", "/camera/image_raw/compressed")
        msg_type = os.environ.get("AI_ROS2_SOURCE_MSG_TYPE", "compressed").strip().lower()

        self._node = Node(node_name)
        self._latest_lock = threading.Lock()
        self._latest_frame: Any | None = None
        self._bridge = None

        if msg_type == "compressed":
            self._subscription = self._node.create_subscription(
                CompressedImage,
                topic,
                self._on_compressed_image,
                qos_depth,
            )
        elif msg_type == "image":
            try:
                from cv_bridge import CvBridge
            except ImportError as exc:
                raise RuntimeError(
                    "AI_ROS2_SOURCE_MSG_TYPE=image requires cv_bridge. "
                    "Use compressed topic or install cv_bridge.",
                ) from exc
            self._bridge = CvBridge()
            self._subscription = self._node.create_subscription(
                Image,
                topic,
                self._on_raw_image,
                qos_depth,
            )
        else:
            raise RuntimeError("AI_ROS2_SOURCE_MSG_TYPE must be 'compressed' or 'image'")

    @property
    def is_live(self) -> bool:
        return True

    def fps(self) -> float:
        return self._fps_hint

    def read(self) -> tuple[bool, Any]:
        deadline = time.monotonic() + self._read_timeout_sec
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False, None

            self._rclpy.spin_once(self._node, timeout_sec=min(0.1, remaining))

            with self._latest_lock:
                if self._latest_frame is not None:
                    frame = self._latest_frame
                    self._latest_frame = None
                    return True, frame

    def release(self) -> None:
        if hasattr(self, "_node"):
            self._node.destroy_node()
        if getattr(self, "_owns_context", False) and self._rclpy.ok():
            self._rclpy.shutdown()

    def _on_compressed_image(self, msg: Any) -> None:
        encoded = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if frame is None:
            return
        with self._latest_lock:
            self._latest_frame = frame

    def _on_raw_image(self, msg: Any) -> None:
        if self._bridge is None:
            return
        frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        with self._latest_lock:
            self._latest_frame = frame
