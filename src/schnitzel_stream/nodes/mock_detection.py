from __future__ import annotations

"""
Mock detection node (frame -> detection).

Intent:
- Phase 4 parity work needs an end-to-end v2 vision demo graph without heavyweight model deps.
- This node emits deterministic detections from frame indices so we can write golden tests.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket


def _as_int(v: Any, *, default: int) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _as_float(v: Any, *, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


@dataclass
class MockDetectorNode:
    """Emit deterministic detection payloads based on `payload.frame_idx`.

    Input packet:
    - kind: frame
    - payload: {frame_idx: int, frame: any}

    Output packet:
    - kind: detection
    - payload: detection dict compatible with `ProtocolV02EventBuilderNode`

    Config:
    - emit_every_n: int (default: 1)
    - event_type: str (default: "ZONE_INTRUSION")
    - object_type: str (default: "PERSON")
    - severity: str (default: "LOW")
    - confidence: float (default: 0.75)
    - track_id: int | "frame_idx" (default: "frame_idx")  (PERSON requires non-null track_id)
    - bbox: {x1,y1,x2,y2} (default: {10,20,200,260})
    - bbox_dx: int (default: 0) : adds dx*frame_idx to x1/x2
    """

    INPUT_KINDS = {"frame"}
    OUTPUT_KINDS = {"detection"}

    node_id: str
    emit_every_n: int
    event_type: str
    object_type: str
    severity: str
    confidence: float
    track_id_mode: str
    track_id_value: int | None
    bbox: dict[str, int]
    bbox_dx: int
    emitted_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self.node_id = str(node_id or "mock_detector")

        self.emit_every_n = max(1, _as_int(cfg.get("emit_every_n", 1), default=1))
        self.event_type = str(cfg.get("event_type", "ZONE_INTRUSION"))
        self.object_type = str(cfg.get("object_type", "PERSON"))
        self.severity = str(cfg.get("severity", "LOW"))
        self.confidence = _as_float(cfg.get("confidence", 0.75), default=0.75)

        track_raw = cfg.get("track_id", "frame_idx")
        if isinstance(track_raw, str) and track_raw.strip() == "frame_idx":
            self.track_id_mode = "frame_idx"
            self.track_id_value = None
        else:
            self.track_id_mode = "const"
            self.track_id_value = _as_int(track_raw, default=0)

        bbox_raw = cfg.get("bbox") if isinstance(cfg.get("bbox"), dict) else {}
        self.bbox = {
            "x1": _as_int(bbox_raw.get("x1", 10), default=10),
            "y1": _as_int(bbox_raw.get("y1", 20), default=20),
            "x2": _as_int(bbox_raw.get("x2", 200), default=200),
            "y2": _as_int(bbox_raw.get("y2", 260), default=260),
        }
        self.bbox_dx = _as_int(cfg.get("bbox_dx", 0), default=0)

        self.emitted_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self.node_id}: expected frame payload as a mapping")
        frame_idx = packet.payload.get("frame_idx")
        if not isinstance(frame_idx, int):
            raise TypeError(f"{self.node_id}: expected payload.frame_idx as int")

        if (frame_idx % self.emit_every_n) != 0:
            return []

        track_id: int | None
        if self.track_id_mode == "frame_idx":
            track_id = int(frame_idx)
        else:
            track_id = self.track_id_value

        bbox = dict(self.bbox)
        if self.bbox_dx:
            bbox["x1"] = int(bbox["x1"] + self.bbox_dx * frame_idx)
            bbox["x2"] = int(bbox["x2"] + self.bbox_dx * frame_idx)

        det: dict[str, Any] = {
            "bbox": bbox,
            "confidence": float(self.confidence),
            "event_type": self.event_type,
            "object_type": self.object_type,
            "severity": self.severity,
        }
        if track_id is not None:
            det["track_id"] = int(track_id)

        meta = dict(packet.meta)
        meta["frame_idx"] = int(frame_idx)
        out = StreamPacket.new(kind="detection", source_id=packet.source_id, payload=det, ts=packet.ts, meta=meta)
        self.emitted_total += 1
        return [out]

    def metrics(self) -> dict[str, int]:
        return {"emitted_total": int(self.emitted_total)}

    def close(self) -> None:
        return
