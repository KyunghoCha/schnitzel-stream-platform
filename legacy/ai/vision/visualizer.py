# Docs: docs/legacy/specs/legacy_pipeline_spec.md
from __future__ import annotations

"""
시각화 모듈

Visualizer 인터페이스를 통해 다양한 시각화 백엔드를 지원합니다.
현재 구현:
- OpencvVisualizer: OpenCV 창을 통한 디버그 시각화
"""

from typing import Protocol, Any
import logging

logger = logging.getLogger(__name__)


class Visualizer(Protocol):
    """시각화 인터페이스 (Protocol)"""

    def show(self, frame: Any, detections: list[dict[str, Any]]) -> None:
        """프레임과 탐지 결과를 시각화합니다."""
        ...

    def close(self) -> None:
        """시각화 리소스를 정리합니다."""
        ...


def draw_bbox(frame: Any, bbox: dict[str, int], label: str, color: tuple[int, int, int] = (0, 255, 0)) -> Any:
    """바운딩 박스를 프레임에 그립니다."""
    if frame is None:
        return frame
    import cv2
    x1 = int(bbox.get("x1", 0))
    y1 = int(bbox.get("y1", 0))
    x2 = int(bbox.get("x2", 0))
    y2 = int(bbox.get("y2", 0))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    if label:
        cv2.putText(frame, label, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return frame


def overlay_detections(frame: Any, detections: list[dict[str, Any]]) -> Any:
    """탐지 결과를 프레임에 오버레이합니다."""
    for det in detections:
        label = f"{det.get('object_type', '')}:{det.get('confidence', 0):.2f}"
        draw_bbox(frame, det.get("bbox", {}), label)
    return frame


class OpencvVisualizer:
    """OpenCV 창을 통한 디버그 시각화"""

    def __init__(self, window_name: str = "AI Pipeline (debug)") -> None:
        self._window_name = window_name
        self._cv2 = None

    def _ensure_cv2(self) -> None:
        if self._cv2 is None:
            import cv2
            self._cv2 = cv2

    def show(self, frame: Any, detections: list[dict[str, Any]]) -> None:
        try:
            self._ensure_cv2()
            # 원본 버퍼 오염 방지를 위해 복사본 사용
            display_frame = frame.copy()
            overlay_detections(display_frame, detections)
            self._cv2.imshow(self._window_name, display_frame)
            self._cv2.waitKey(1)
        except Exception as exc:
            logger.warning("visualization failed: %s", exc)

    def close(self) -> None:
        if self._cv2 is not None:
            try:
                self._cv2.destroyWindow(self._window_name)
            except Exception:
                pass


class NullVisualizer:
    """아무것도 하지 않는 Null Object 패턴 시각화"""

    def show(self, frame: Any, detections: list[dict[str, Any]]) -> None:
        pass

    def close(self) -> None:
        pass
