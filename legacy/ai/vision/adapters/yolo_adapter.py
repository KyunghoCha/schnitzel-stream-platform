# Docs: docs/packs/vision/ops/ai/model_yolo_run.md, docs/packs/vision/model_interface.md
from __future__ import annotations

# YOLO 어댑터 스켈레톤 (미리 학습된 베이스라인)
# Ultralytics YOLO 사용; 빠른 로컬 검증용.

from dataclasses import dataclass
from typing import Any
import logging
import os

from ai.pipeline.model_adapter import ModelAdapter
from ai.vision.trackers.tracker_factory import build_tracker
from ai.vision.class_mapping import DEFAULT_CLASS_MAP, ClassMapEntry, load_class_map

logger = logging.getLogger(__name__)


@dataclass
class YOLOAdapterConfig:
    """YOLO 어댑터 설정 (DI-friendly)."""
    model_path: str = ""
    conf_threshold: float = 0.25
    device: str = "auto"
    tracker_type: str = "none"
    tracker_max_age: int = 30
    tracker_min_hits: int = 1
    tracker_iou: float = 0.3
    class_map_path: str | None = None

    @classmethod
    def from_env(cls) -> YOLOAdapterConfig:
        """환경 변수에서 설정 로드."""
        return cls(
            model_path=os.getenv("YOLO_MODEL_PATH", "").strip(),
            conf_threshold=float(os.getenv("YOLO_CONF", "0.25")),
            device=os.getenv("YOLO_DEVICE", "auto").strip() or "auto",
            tracker_type=os.getenv("TRACKER_TYPE", "none"),
            tracker_max_age=int(os.getenv("TRACKER_MAX_AGE", "30")),
            tracker_min_hits=int(os.getenv("TRACKER_MIN_HITS", "1")),
            tracker_iou=float(os.getenv("TRACKER_IOU", "0.3")),
            class_map_path=os.getenv("MODEL_CLASS_MAP_PATH", "").strip() or None,
        )


class YOLOAdapter(ModelAdapter):
    def __init__(self, config: YOLOAdapterConfig | None = None) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise ImportError(
                "ultralytics is required for YOLOAdapter. Install it or use another adapter."
            ) from exc

        import torch

        cfg = config or YOLOAdapterConfig.from_env()

        if not cfg.model_path:
            raise RuntimeError("YOLO_MODEL_PATH is required for YOLOAdapter")
        self._model = YOLO(cfg.model_path)
        self._conf = cfg.conf_threshold
        self._device = cfg.device
        if self._device == "auto":
            self._device = "0" if torch.cuda.is_available() else "cpu"
        self._track_seq = 0
        self._tracker = build_tracker(cfg.tracker_type, cfg.tracker_max_age, cfg.tracker_min_hits, cfg.tracker_iou)
        self._class_map: dict[int, ClassMapEntry] = load_class_map(cfg.class_map_path) or dict(DEFAULT_CLASS_MAP)

    def infer(self, frame: Any) -> list[dict[str, Any]]:
        # 참고: 최소 스켈레톤입니다. 레이블에 맞게 클래스 매핑을 업데이트하세요.
        results = self._model.predict(frame, conf=self._conf, verbose=False, device=self._device)
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
