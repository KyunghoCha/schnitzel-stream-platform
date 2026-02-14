# Docs: docs/implementation/25-model-tracking/spec.md
# 선택적 ByteTrack 래퍼; 의존성이 설치된 경우에만 활성화.
from __future__ import annotations

from typing import Any

import numpy as np

from ai.vision.geometry import iou_bbox_dict

try:  # pragma: no cover - optional dependency
    from yolox.tracker.byte_tracker import BYTETracker  # type: ignore
    _BYTETRACK_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    BYTETracker = None
    _BYTETRACK_AVAILABLE = False


class ByteTrackTracker:
    # BYTETracker에 대한 얇은 래퍼 (선택 사항)
    def __init__(self, max_age: int = 30, min_hits: int = 1, iou_thres: float = 0.3) -> None:
        if not _BYTETRACK_AVAILABLE:
            raise ImportError("ByteTrack is not available. Install yolox/bytetrack deps.")
        args = {
            "track_thresh": 0.5,
            "track_buffer": max_age,
            "match_thresh": iou_thres,
            "mot20": False,
        }
        self._tracker = BYTETracker(args, frame_rate=30)
        self._min_hits = max(1, min_hits)

    def update(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not detections:
            return detections
        dets = []
        for d in detections:
            bbox = d.get("bbox")
            if not isinstance(bbox, dict):
                continue
            score = float(d.get("confidence", 0.0))
            dets.append([bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"], score])
        if not dets:
            return detections
        dets_np = np.array(dets, dtype=float)
        online_targets = self._tracker.update(dets_np, [1, 1], [1, 1])
        # 가장 가까운 bbox로 다시 매핑
        for t in online_targets:
            tlbr = t.tlbr
            tid = int(t.track_id)
            # 가장 가까운 감지 bbox에 할당
            best_iou = 0.0
            best_idx = None
            for i, d in enumerate(detections):
                bbox = d.get("bbox")
                if not isinstance(bbox, dict):
                    continue
                iou = _iou_bbox(tlbr, bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = i
            if best_idx is not None:
                detections[best_idx]["track_id"] = tid
        return detections


def _iou_bbox(tlbr: list[float], bbox: dict[str, int]) -> float:
    a = {"x1": int(tlbr[0]), "y1": int(tlbr[1]), "x2": int(tlbr[2]), "y2": int(tlbr[3])}
    return iou_bbox_dict(a, bbox)


def bytetrack_available() -> bool:
    return _BYTETRACK_AVAILABLE
