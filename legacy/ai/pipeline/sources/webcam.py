# Docs: docs/legacy/specs/legacy_pipeline_spec.md
from __future__ import annotations

# 웹캠 프레임 소스

from dataclasses import dataclass
import cv2


@dataclass
class WebcamSource:
    """웹캠 VideoCapture (device index 기반)"""

    device_index: int
    supports_reconnect: bool = False

    def __post_init__(self) -> None:
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open webcam device: {self.device_index}")

    def read(self) -> tuple[bool, object]:
        return self.cap.read()

    def release(self) -> None:
        self.cap.release()

    @property
    def is_live(self) -> bool:
        return True

    def fps(self) -> float:
        return float(self.cap.get(cv2.CAP_PROP_FPS))
