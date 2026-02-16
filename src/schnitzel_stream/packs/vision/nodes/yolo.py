from __future__ import annotations

"""
YOLO + OpenCV overlay nodes (frame -> frame).

Intent:
- Keep model inference and display as plugins so the core runtime remains domain-neutral.
- Preserve `kind=frame` through the detector node to avoid introducing a join node for overlay.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.project import resolve_project_root

try:  # pragma: no cover
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]

try:  # pragma: no cover
    from ultralytics import YOLO as _YOLO
except Exception:  # pragma: no cover
    _YOLO = None  # type: ignore[assignment]


def _as_float(v: Any, *, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _as_int(v: Any, *, default: int) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _resolve_model_path(raw: Any) -> Path:
    model_raw = str(raw or "").strip() or "models/yolov8n.pt"
    p = Path(model_raw)
    if not p.is_absolute():
        # Intent: keep relative model paths stable for subprocess runs and IDE terminals.
        p = resolve_project_root() / p
    return p.resolve()


def _parse_classes(raw: Any) -> list[int] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        out: list[int] = []
        for part in text.split(","):
            token = part.strip()
            if not token:
                continue
            out.append(int(token))
        return out or None
    if isinstance(raw, (list, tuple, set)):
        out = [int(x) for x in raw]
        return out or None
    return None


def _xyxy_from_box(box: Any) -> tuple[int, int, int, int] | None:
    xyxy = getattr(box, "xyxy", None)
    if xyxy is None:
        return None
    if hasattr(xyxy, "tolist"):
        xyxy = xyxy.tolist()
    if isinstance(xyxy, (list, tuple)) and xyxy and isinstance(xyxy[0], (list, tuple)):
        xyxy = xyxy[0]
    if not isinstance(xyxy, (list, tuple)) or len(xyxy) < 4:
        return None
    try:
        x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
    except Exception:
        return None
    return (int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)))


def _scalar_float(raw: Any, *, default: float) -> float:
    try:
        if hasattr(raw, "item"):
            return float(raw.item())
        if isinstance(raw, (list, tuple)) and raw:
            return float(raw[0])
        return float(raw)
    except Exception:
        return float(default)


def _scalar_int(raw: Any, *, default: int) -> int:
    try:
        if hasattr(raw, "item"):
            return int(raw.item())
        if isinstance(raw, (list, tuple)) and raw:
            return int(raw[0])
        return int(raw)
    except Exception:
        return int(default)


def _resolve_names(result: Any, fallback: Any) -> dict[int, str]:
    raw = getattr(result, "names", None)
    if raw is None:
        raw = fallback
    if isinstance(raw, Mapping):
        out: dict[int, str] = {}
        for k, v in raw.items():
            try:
                out[int(k)] = str(v)
            except Exception:
                continue
        return out
    if isinstance(raw, (list, tuple)):
        return {int(i): str(v) for i, v in enumerate(raw)}
    return {}


@dataclass
class YoloV8DetectorNode:
    """Run YOLOv8 inference and attach `payload.detections` to frame packets.

    Input packet:
    - kind: frame
    - payload: {frame: np.ndarray(BGR), frame_idx: int, ...}

    Output packet:
    - kind: frame
    - payload: input payload + detections[]

    Config:
    - model_path: str (default: models/yolov8n.pt)
    - conf: float (default: 0.25)
    - iou: float (default: 0.45)
    - max_det: int (default: 100)
    - classes: list[int] | "0,1,2" (optional)
    - device: str (optional, e.g. "cpu", "0")
    """

    INPUT_KINDS = {"frame"}
    OUTPUT_KINDS = {"frame"}
    INPUT_PROFILE = "inproc_any"
    OUTPUT_PROFILE = "inproc_any"

    node_id: str
    model_path: str
    conf: float
    iou: float
    max_det: int
    classes: list[int] | None
    device: str | None
    emitted_total: int = 0
    detected_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        if _YOLO is None:
            raise ImportError("YoloV8DetectorNode requires ultralytics (pip install -r requirements-model.txt)")

        cfg = dict(config or {})
        self.node_id = str(node_id or "yolo_v8_detector")

        model_path = _resolve_model_path(cfg.get("model_path"))
        if not model_path.exists():
            raise FileNotFoundError(f"YOLO model file not found: {model_path}")
        self.model_path = str(model_path)

        self.conf = max(0.0, min(1.0, _as_float(cfg.get("conf", 0.25), default=0.25)))
        self.iou = max(0.0, min(1.0, _as_float(cfg.get("iou", 0.45), default=0.45)))
        self.max_det = max(1, _as_int(cfg.get("max_det", 100), default=100))
        self.classes = _parse_classes(cfg.get("classes"))

        device_raw = str(cfg.get("device", "")).strip()
        self.device = device_raw if device_raw else None

        self._model = _YOLO(self.model_path)
        self._model_names = getattr(self._model, "names", {})

        self.emitted_total = 0
        self.detected_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self.node_id}: expected frame payload as a mapping")
        frame = packet.payload.get("frame")
        if frame is None:
            raise TypeError(f"{self.node_id}: expected payload.frame")

        kwargs: dict[str, Any] = {
            "verbose": False,
            "conf": float(self.conf),
            "iou": float(self.iou),
            "max_det": int(self.max_det),
        }
        if self.classes:
            kwargs["classes"] = list(self.classes)
        if self.device:
            kwargs["device"] = str(self.device)

        results = self._model.predict(frame, **kwargs)
        result0 = results[0] if results else None
        names = _resolve_names(result0, self._model_names)

        detections: list[dict[str, Any]] = []
        boxes = getattr(result0, "boxes", []) if result0 is not None else []
        for box in boxes:
            xyxy = _xyxy_from_box(box)
            if xyxy is None:
                continue

            cls_id = _scalar_int(getattr(box, "cls", -1), default=-1)
            conf = _scalar_float(getattr(box, "conf", 0.0), default=0.0)
            x1, y1, x2, y2 = xyxy

            det: dict[str, Any] = {
                "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                "confidence": float(conf),
                "class_id": int(cls_id),
                "class_name": str(names.get(int(cls_id), str(cls_id))),
            }
            detections.append(det)

        payload = dict(packet.payload)
        payload["detections"] = detections

        meta = dict(packet.meta)
        meta["detection_count"] = int(len(detections))
        meta["model"] = str(Path(self.model_path).name)

        out = StreamPacket.new(
            kind="frame",
            source_id=packet.source_id,
            payload=payload,
            ts=packet.ts,
            meta=meta,
        )

        self.emitted_total += 1
        self.detected_total += int(len(detections))
        return [out]

    def metrics(self) -> dict[str, int]:
        return {"emitted_total": int(self.emitted_total), "detected_total": int(self.detected_total)}

    def close(self) -> None:
        return


@dataclass
class OpenCvBboxDisplaySink:
    """Display frames with detection boxes in an OpenCV window.

    Input packet:
    - kind: frame
    - payload.frame: np.ndarray(BGR)
    - payload.detections: list[{bbox, class_name, confidence}] (optional)

    Config:
    - window_name: str (default: "Schnitzel Stream - YOLO")
    - wait_key_ms: int (default: 1)
    - line_thickness: int (default: 2)
    - font_scale: float (default: 0.6)
    - color_bgr: [b,g,r] (default: [48, 220, 48])
    - show_stats: bool (default: true)
    - stop_on_quit_key: bool (default: true)
    - forward: bool (default: false)
    """

    INPUT_KINDS = {"frame"}
    OUTPUT_KINDS = {"*"}
    INPUT_PROFILE = "inproc_any"
    OUTPUT_PROFILE = "inproc_any"

    node_id: str
    window_name: str
    wait_key_ms: int
    line_thickness: int
    font_scale: float
    color_bgr: tuple[int, int, int]
    show_stats: bool
    stop_on_quit_key: bool
    forward: bool

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        if cv2 is None:
            raise ImportError("OpenCvBboxDisplaySink requires opencv-python (GUI build)")

        cfg = dict(config or {})
        self.node_id = str(node_id or "opencv_bbox_display")
        self.window_name = str(cfg.get("window_name", "Schnitzel Stream - YOLO"))
        self.wait_key_ms = max(1, _as_int(cfg.get("wait_key_ms", 1), default=1))
        self.line_thickness = max(1, _as_int(cfg.get("line_thickness", 2), default=2))
        self.font_scale = max(0.1, _as_float(cfg.get("font_scale", 0.6), default=0.6))

        color_raw = cfg.get("color_bgr", [48, 220, 48])
        if isinstance(color_raw, (list, tuple)) and len(color_raw) >= 3:
            b = max(0, min(255, _as_int(color_raw[0], default=48)))
            g = max(0, min(255, _as_int(color_raw[1], default=220)))
            r = max(0, min(255, _as_int(color_raw[2], default=48)))
            self.color_bgr = (b, g, r)
        else:
            self.color_bgr = (48, 220, 48)

        self.show_stats = bool(cfg.get("show_stats", True))
        self.stop_on_quit_key = bool(cfg.get("stop_on_quit_key", True))
        self.forward = bool(cfg.get("forward", False))

        self._shown_total = 0

    def _draw_box(self, frame: Any, det: dict[str, Any]) -> None:
        assert cv2 is not None
        bbox = det.get("bbox")
        if not isinstance(bbox, dict):
            return
        x1 = _as_int(bbox.get("x1"), default=0)
        y1 = _as_int(bbox.get("y1"), default=0)
        x2 = _as_int(bbox.get("x2"), default=0)
        y2 = _as_int(bbox.get("y2"), default=0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), self.color_bgr, self.line_thickness)

        class_name = str(det.get("class_name", det.get("class_id", "?")))
        conf = _as_float(det.get("confidence", 0.0), default=0.0)
        label = f"{class_name} {conf:.2f}"
        cv2.putText(
            frame,
            label,
            (x1, max(15, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            self.font_scale,
            self.color_bgr,
            max(1, self.line_thickness - 1),
            cv2.LINE_AA,
        )

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        assert cv2 is not None
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self.node_id}: expected frame payload as a mapping")
        frame = packet.payload.get("frame")
        if frame is None:
            raise TypeError(f"{self.node_id}: expected payload.frame")

        # Intent: draw on a copy so upstream/downstream nodes never observe overlay mutations.
        canvas = frame.copy() if hasattr(frame, "copy") else frame
        detections_raw = packet.payload.get("detections", [])
        detections = detections_raw if isinstance(detections_raw, list) else []
        for det in detections:
            if isinstance(det, dict):
                self._draw_box(canvas, det)

        if self.show_stats:
            frame_idx = packet.payload.get("frame_idx", "?")
            stat_text = f"src={packet.source_id} frame={frame_idx} det={len(detections)}"
            cv2.putText(
                canvas,
                stat_text,
                (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                self.font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        try:
            cv2.imshow(self.window_name, canvas)
            key = int(cv2.waitKey(self.wait_key_ms) & 0xFF)
        except Exception as exc:
            raise RuntimeError(
                "OpenCvBboxDisplaySink failed to render window. "
                "Install GUI-enabled opencv-python and run from a desktop session."
            ) from exc

        self._shown_total += 1

        if self.stop_on_quit_key and key in (27, ord("q"), ord("Q")):
            # Intent: allow operator shutdown from CV window without external process signals.
            raise KeyboardInterrupt("quit key pressed in OpenCvBboxDisplaySink")

        if self.forward:
            return [packet]
        return []

    def metrics(self) -> dict[str, int]:
        return {"shown_total": int(self._shown_total)}

    def close(self) -> None:
        if cv2 is None:
            return
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            return
