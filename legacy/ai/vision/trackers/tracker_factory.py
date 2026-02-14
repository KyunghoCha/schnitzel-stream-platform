# Docs: docs/implementation/25-model-tracking/spec.md
# 설정에 따른 트래커 선택; 어댑터를 정책과 분리 유지.
from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from ai.vision.trackers.tracker_iou import IOUTracker
from ai.vision.trackers.tracker_bytetrack import ByteTrackTracker, bytetrack_available

logger = logging.getLogger(__name__)


class Tracker(Protocol):
    """트래커 공통 인터페이스"""

    def update(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ...


def build_tracker(
    tracker_type: str, max_age: int, min_hits: int, iou_thres: float
) -> Tracker | None:
    t = tracker_type.strip().lower()
    if t in ("", "none"):
        return None
    if t == "iou":
        return IOUTracker(max_age=max_age, min_hits=min_hits, iou_thres=iou_thres)
    if t == "bytetrack":
        if not bytetrack_available():
            logger.warning("ByteTrack not available, fallback to IOU tracker")
            return IOUTracker(max_age=max_age, min_hits=min_hits, iou_thres=iou_thres)
        return ByteTrackTracker(max_age=max_age, min_hits=min_hits, iou_thres=iou_thres)
    logger.warning("unsupported TRACKER_TYPE=%s, fallback to none", tracker_type)
    return None


def build_tracker_from_env() -> Tracker | None:
    """환경변수에서 트래커 설정을 읽어 생성한다. 어댑터 공통 헬퍼."""
    tracker_type = os.getenv("TRACKER_TYPE", "none")
    max_age = int(os.getenv("TRACKER_MAX_AGE", "30"))
    min_hits = int(os.getenv("TRACKER_MIN_HITS", "1"))
    iou_thres = float(os.getenv("TRACKER_IOU", "0.3"))
    return build_tracker(tracker_type, max_age, min_hits, iou_thres)
