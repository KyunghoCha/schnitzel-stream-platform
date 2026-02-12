# Demo PPE adapter (non-production)
# Docs: docs/ops/ai/demo/ppe_demo.md
# Intended for demo runs; not wired as a default adapter.

from __future__ import annotations
from typing import Any
import logging
import os

from ai.pipeline.model_adapter import ModelAdapter
from ai.vision.trackers.tracker_factory import build_tracker
from ai.vision.class_mapping import ClassMapEntry, load_class_map

class YOLOPPEAdapter(ModelAdapter):
    def __init__(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise ImportError(
                "ultralytics is required for YOLOPPEAdapter. Install it or use another adapter."
            ) from exc

        model_path = os.getenv("YOLO_PPE_MODEL_PATH", "").strip()
        if not model_path:
            raise RuntimeError("YOLO_PPE_MODEL_PATH is required for YOLOPPEAdapter")
        self._model = YOLO(model_path)
        self._conf = float(os.getenv("YOLO_PPE_CONF", "0.25"))
        self._track_seq = 0
        self._tracker = self._build_tracker()
        class_map_path = os.getenv("MODEL_CLASS_MAP_PATH_PPE", "").strip() or None
        self._class_map = load_class_map(class_map_path)
        if not self._class_map:
            # Default PPE mapping (demo): map all classes to PPE_VIOLATION/UNKNOWN
            self._class_map = {
                0: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
                1: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
                2: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
                3: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
                4: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
                5: ClassMapEntry(event_type="PPE_VIOLATION", object_type="UNKNOWN", severity="LOW"),
            }

    def _build_tracker(self):
        tracker_type = os.getenv("TRACKER_TYPE", "none")
        max_age = int(os.getenv("TRACKER_MAX_AGE", "30"))
        min_hits = int(os.getenv("TRACKER_MIN_HITS", "1"))
        iou_thres = float(os.getenv("TRACKER_IOU", "0.3"))
        return build_tracker(tracker_type, max_age, min_hits, iou_thres)

    def infer(self, frame: Any) -> list[dict[str, Any]]:
        results = self._model.predict(frame, conf=self._conf, verbose=False)
        payloads: list[dict[str, Any]] = []
        for r in results:
            if r.boxes is None:
                continue
            for b in r.boxes:
                xyxy = b.xyxy[0].tolist()
                cls_id = int(b.cls[0])
                conf = float(b.conf[0])
                mapping = self._class_map.get(cls_id)
                if mapping is None:
                    continue
                track_id = self._track_seq
                self._track_seq += 1
                payloads.append(
                    {
                        "event_type": mapping.event_type,
                        "object_type": mapping.object_type,
                        "severity": mapping.severity,
                        "track_id": track_id,
                        "bbox": {
                            "x1": int(xyxy[0]),
                            "y1": int(xyxy[1]),
                            "x2": int(xyxy[2]),
                            "y2": int(xyxy[3]),
                        },
                        "confidence": conf,
                    }
                )
        if self._tracker is not None:
            return self._tracker.update(payloads)
        return payloads
