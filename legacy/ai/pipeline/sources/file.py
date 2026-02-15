# Docs: docs/specs/legacy_pipeline_spec.md
from __future__ import annotations

# 파일 기반 프레임 소스

from dataclasses import dataclass
import cv2


@dataclass
class FileSource:
    """MP4 파일 기반 VideoCapture"""

    path: str
    loop: bool = False
    supports_reconnect: bool = False

    def __post_init__(self) -> None:
        self.cap = cv2.VideoCapture(self.path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {self.path}")

    def read(self) -> tuple[bool, object]:
        ret, frame = self.cap.read()
        if not ret and self.loop:
            # 파일 끝에 도달하면 처음으로 되돌림
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        return ret, frame

    def release(self) -> None:
        if self.cap:
            self.cap.release()

    @property
    def is_live(self) -> bool:
        return False

    def fps(self) -> float:
        return float(self.cap.get(cv2.CAP_PROP_FPS))
