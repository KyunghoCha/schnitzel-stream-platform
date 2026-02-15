# Docs: docs/implementation/25-model-tracking/spec.md, docs/packs/vision/model_interface.md
# 베이스라인으로 사용되는 경량 IoU 기반 트래커.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.vision.geometry import iou_bbox_dict as _iou


@dataclass
class _Track:
    track_id: int
    bbox: dict[str, int]
    age: int = 0
    hits: int = 1


# track_id가 반드시 필요한 object_type 목록 (프로토콜 요구사항)
_REQUIRE_TRACK_TYPES = frozenset({"PERSON"})


class IOUTracker:
    # 단순 IoU 트래커 (프로세스별)
    def __init__(
        self, max_age: int = 30, min_hits: int = 1, iou_thres: float = 0.3,
        require_track_types: frozenset[str] = _REQUIRE_TRACK_TYPES,
    ) -> None:
        self._max_age = max(1, max_age)
        self._min_hits = max(1, min_hits)
        self._iou_thres = max(0.0, min(1.0, iou_thres))
        self._require_track_types = require_track_types
        self._tracks: list[_Track] = []
        self._next_id = 0

    def update(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # 모든 트랙의 수명(age) 증가
        for t in self._tracks:
            t.age += 1

        # 그리디 IoU로 감지와 트랙 매칭
        unmatched_det_idx = set(range(len(detections)))
        for t in list(self._tracks):
            best_iou = 0.0
            best_idx = None
            for i in list(unmatched_det_idx):
                det = detections[i]
                bbox = det.get("bbox")
                if not isinstance(bbox, dict):
                    continue
                iou = _iou(t.bbox, bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = i
            if best_idx is not None and best_iou >= self._iou_thres:
                det = detections[best_idx]
                t.bbox = det["bbox"]
                t.age = 0
                t.hits += 1
                det["track_id"] = t.track_id
                unmatched_det_idx.remove(best_idx)

        # 매칭되지 않은 감지에 대해 새 트랙 생성
        for i in sorted(unmatched_det_idx):
            det = detections[i]
            bbox = det.get("bbox")
            if not isinstance(bbox, dict):
                continue
            track_id = self._next_id
            self._next_id += 1
            self._tracks.append(_Track(track_id=track_id, bbox=bbox))
            det["track_id"] = track_id

        # 오래된 트랙정리
        self._tracks = [t for t in self._tracks if t.age <= self._max_age]

        # 프로토콜 필수 object_type에 대해 track_id 보장
        for det in detections:
            if det.get("object_type") in self._require_track_types and det.get("track_id") is None:
                det["track_id"] = self._next_id
                self._next_id += 1
        return detections
