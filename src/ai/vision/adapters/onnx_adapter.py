# Docs: docs/ops/ai/model_yolo_run.md, docs/specs/model_interface.md
from __future__ import annotations

# YOLOv8용 ONNX 어댑터 (단일 클래스 베이스라인: PERSON)

from dataclasses import dataclass, field
from typing import Any
import logging
import os

import cv2
import numpy as np
import onnxruntime as ort

from ai.pipeline.model_adapter import ModelAdapter
from ai.vision.trackers.tracker_factory import build_tracker
from ai.vision.class_mapping import DEFAULT_CLASS_MAP, ClassMapEntry, load_class_map

logger = logging.getLogger(__name__)


@dataclass
class ONNXAdapterConfig:
    """ONNX 어댑터 설정 (DI-friendly)."""
    model_path: str = ""
    providers: list[str] = field(default_factory=lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"])
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    tracker_type: str = "none"
    tracker_max_age: int = 30
    tracker_min_hits: int = 1
    tracker_iou: float = 0.3
    class_map_path: str | None = None

    @classmethod
    def from_env(cls) -> ONNXAdapterConfig:
        """환경 변수에서 설정 로드."""
        providers_raw = os.getenv("ONNX_PROVIDERS", "").strip()
        providers = [p.strip() for p in providers_raw.split(",") if p.strip()] or [
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]
        return cls(
            model_path=os.getenv("ONNX_MODEL_PATH", "").strip(),
            providers=providers,
            conf_threshold=float(os.getenv("ONNX_CONF", "0.25")),
            iou_threshold=float(os.getenv("ONNX_IOU", "0.45")),
            tracker_type=os.getenv("TRACKER_TYPE", "none"),
            tracker_max_age=int(os.getenv("TRACKER_MAX_AGE", "30")),
            tracker_min_hits=int(os.getenv("TRACKER_MIN_HITS", "1")),
            tracker_iou=float(os.getenv("TRACKER_IOU", "0.3")),
            class_map_path=os.getenv("MODEL_CLASS_MAP_PATH", "").strip() or None,
        )


def _letterbox(image: np.ndarray, new_shape: tuple[int, int] = (640, 640)) -> tuple[np.ndarray, float, tuple[int, int]]:
    h, w = image.shape[:2]
    new_w, new_h = new_shape
    r = min(new_w / w, new_h / h)
    resized = cv2.resize(image, (int(round(w * r)), int(round(h * r))), interpolation=cv2.INTER_LINEAR)
    pad_w = new_w - resized.shape[1]
    pad_h = new_h - resized.shape[0]
    top = pad_h // 2
    bottom = pad_h - top
    left = pad_w // 2
    right = pad_w - left
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return padded, r, (left, top)


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_thres: float) -> list[int]:
    idxs = scores.argsort()[::-1]
    keep: list[int] = []
    while idxs.size > 0:
        i = idxs[0]
        keep.append(int(i))
        if idxs.size == 1:
            break
        rest = idxs[1:]
        iou = _iou(boxes[i], boxes[rest])
        idxs = rest[iou < iou_thres]
    return keep


def _iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    x1 = np.maximum(box[0], boxes[:, 0])
    y1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[2], boxes[:, 2])
    y2 = np.minimum(box[3], boxes[:, 3])
    inter = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    area1 = (box[2] - box[0]) * (box[3] - box[1])
    area2 = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    return inter / (area1 + area2 - inter + 1e-9)


class ONNXYOLOAdapter(ModelAdapter):
    def __init__(self, config: ONNXAdapterConfig | None = None) -> None:
        cfg = config or ONNXAdapterConfig.from_env()

        if not cfg.model_path:
            raise RuntimeError("ONNX_MODEL_PATH is required for ONNXYOLOAdapter")

        self._sess = ort.InferenceSession(cfg.model_path, providers=cfg.providers)
        self._input_name = self._sess.get_inputs()[0].name
        self._output_name = self._sess.get_outputs()[0].name
        self._conf = cfg.conf_threshold
        self._iou = cfg.iou_threshold
        self._track_seq = 0
        self._tracker = build_tracker(cfg.tracker_type, cfg.tracker_max_age, cfg.tracker_min_hits, cfg.tracker_iou)
        self._class_map: dict[int, ClassMapEntry] = load_class_map(cfg.class_map_path) or dict(DEFAULT_CLASS_MAP)

        in_shape = self._sess.get_inputs()[0].shape
        # (1,3,h,w) 예상. 가변일 경우 기본값 640.
        self._in_h = int(in_shape[2]) if isinstance(in_shape[2], int) else 640
        self._in_w = int(in_shape[3]) if isinstance(in_shape[3], int) else 640

    def _preprocess(self, img: np.ndarray) -> tuple[np.ndarray, float, tuple[int, int]]:
        """프레임을 모델 입력 형식으로 변환한다."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        padded, ratio, pad = _letterbox(img_rgb, (self._in_w, self._in_h))
        inp = padded.astype(np.float32) / 255.0
        inp = np.transpose(inp, (2, 0, 1))
        inp = np.expand_dims(inp, 0)
        return inp, ratio, pad

    def _decode_output(
        self, out: np.ndarray, ratio: float, pad: tuple[int, int], img_shape: tuple[int, int],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """모델 출력을 원본 좌표계의 xyxy/conf/class_ids로 변환한다."""
        if out.ndim == 3:
            out = out[0]
        if out.shape[0] < out.shape[1]:
            out = out.transpose(1, 0)

        boxes = out[:, :4]
        class_scores = out[:, 4:]
        if class_scores.shape[1] < 1:
            return np.array([]), np.array([]), np.array([])

        class_ids = class_scores.argmax(axis=1)
        conf = class_scores.max(axis=1)
        keep = conf >= self._conf
        boxes, conf, class_ids = boxes[keep], conf[keep], class_ids[keep]
        if boxes.size == 0:
            return np.array([]), np.array([]), np.array([])

        # xywh -> xyxy
        xyxy = np.zeros_like(boxes)
        xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2

        keep_idx = _nms(xyxy, conf, self._iou)
        xyxy, conf, class_ids = xyxy[keep_idx], conf[keep_idx], class_ids[keep_idx]

        # 레터박스 해제 (de-letterbox)
        pad_x, pad_y = pad
        xyxy[:, [0, 2]] -= pad_x
        xyxy[:, [1, 3]] -= pad_y
        xyxy /= ratio

        return xyxy, conf, class_ids

    def _to_payloads(
        self, xyxy: np.ndarray, conf: np.ndarray, class_ids: np.ndarray, img_shape: tuple[int, int],
    ) -> list[dict[str, Any]]:
        """numpy 배열을 페이로드 dict 리스트로 변환한다."""
        h, w = img_shape
        payloads: list[dict[str, Any]] = []
        for box, c, cls_id in zip(xyxy, conf, class_ids):
            x1 = int(max(0, min(w, box[0])))
            y1 = int(max(0, min(h, box[1])))
            x2 = int(max(0, min(w, box[2])))
            y2 = int(max(0, min(h, box[3])))
            if x2 <= x1 or y2 <= y1:
                continue
            mapping = self._class_map.get(int(cls_id))
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
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "confidence": float(c),
                }
            )
        return payloads

    def infer(self, frame: Any) -> list[dict[str, Any]]:
        if frame is None or not isinstance(frame, np.ndarray):
            return []

        inp, ratio, pad = self._preprocess(frame)
        out = self._sess.run([self._output_name], {self._input_name: inp})[0]
        xyxy, conf, class_ids = self._decode_output(out, ratio, pad, frame.shape[:2])
        if xyxy.size == 0:
            return []
        payloads = self._to_payloads(xyxy, conf, class_ids, frame.shape[:2])
        if self._tracker is not None:
            return self._tracker.update(payloads)
        return payloads
