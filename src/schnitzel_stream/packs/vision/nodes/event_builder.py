from __future__ import annotations

"""
Event builder nodes (Protocol v0.2).

Intent:
- Provide a platform-owned event builder so Phase 4 can remove legacy `ai.*` code.
- Emit *deterministic* `event_id` and `meta.idempotency_key` to support at-least-once delivery
  with dedup at the durable queue boundary (Phase 2).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import NAMESPACE_DNS, uuid4, uuid5

from schnitzel_stream.packet import StreamPacket

_EVENT_ID_NAMESPACE = uuid5(NAMESPACE_DNS, "schnitzel_stream:event_protocol_v0.2")


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_event_scaffold(*, site_id: str, camera_id: str, ts: str | None) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "ts": ts or _now_iso_utc(),
        "site_id": site_id,
        "camera_id": camera_id,
        "event_type": "",
        "object_type": "",
        "severity": "",
        "track_id": None,
        "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
        "confidence": 0.0,
        "zone": {"zone_id": "", "inside": False},
        "snapshot_path": None,
        "sensor": None,
    }


def _is_valid_detection(det: dict[str, Any]) -> bool:
    required = ("bbox", "confidence", "event_type", "object_type", "severity")
    if any(k not in det for k in required):
        return False
    bbox = det.get("bbox")
    if not isinstance(bbox, dict):
        return False
    for key in ("x1", "y1", "x2", "y2"):
        if key not in bbox:
            return False
    if det.get("object_type") == "PERSON" and det.get("track_id") is None:
        return False
    return True


def _event_idempotency_key(*, site_id: str, camera_id: str, packet_ts: str, det: dict[str, Any]) -> str:
    bbox = det.get("bbox", {})
    bbox_s = ""
    if isinstance(bbox, dict):
        bbox_s = f"{bbox.get('x1','')}:{bbox.get('y1','')}:{bbox.get('x2','')}:{bbox.get('y2','')}"
    track_id = det.get("track_id")
    track_s = str(track_id) if track_id is not None else "na"
    return (
        "event:"
        f"{site_id}:{camera_id}:{det.get('event_type','')}:{det.get('object_type','')}:{track_s}:"
        f"{packet_ts}:{bbox_s}"
    )


@dataclass
class ProtocolV02EventBuilderNode:
    """Convert `kind=detection` packets into backend `kind=event` packets.

    Input payload formats:
    - dict: a single detection
    - list[dict]: multiple detections for the same frame/timestamp

    Detection dict fields (required):
    - bbox: {x1,y1,x2,y2}
    - confidence: float
    - event_type: str
    - object_type: str
    - severity: str
    - track_id: int (required if object_type == "PERSON")

    Config:
    - site_id: str (required)
    - camera_id: str (optional; default: packet.source_id)
    """

    INPUT_KINDS = {"detection"}
    OUTPUT_KINDS = {"event"}

    node_id: str
    site_id: str
    camera_id: str | None = None
    emitted_total: int = 0
    skipped_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        site_id = str(cfg.get("site_id", "")).strip()
        if not site_id:
            raise ValueError("ProtocolV02EventBuilderNode requires config.site_id")

        self.node_id = str(node_id or "event_builder")
        self.site_id = site_id
        camera_id = cfg.get("camera_id")
        self.camera_id = str(camera_id).strip() if isinstance(camera_id, str) and camera_id.strip() else None

        self.emitted_total = 0
        self.skipped_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        payload = packet.payload
        if payload is None:
            return []

        if isinstance(payload, dict):
            dets: list[dict[str, Any]] = [payload]
        elif isinstance(payload, list):
            dets = [d for d in payload if isinstance(d, dict)]
        else:
            raise TypeError(f"{self.node_id}: detection payload must be dict|list[dict]|None")

        camera_id = self.camera_id or str(packet.source_id)
        out: list[StreamPacket] = []
        for det in dets:
            if not _is_valid_detection(det):
                self.skipped_total += 1
                continue

            idempotency_key = _event_idempotency_key(
                site_id=self.site_id,
                camera_id=camera_id,
                packet_ts=str(packet.ts),
                det=det,
            )
            event_id = str(uuid5(_EVENT_ID_NAMESPACE, idempotency_key))

            event = build_event_scaffold(site_id=self.site_id, camera_id=camera_id, ts=str(packet.ts))
            event["event_id"] = event_id
            event["event_type"] = det["event_type"]
            event["object_type"] = det["object_type"]
            event["severity"] = det["severity"]
            event["confidence"] = float(det["confidence"])
            event["bbox"] = det["bbox"]
            event["track_id"] = det.get("track_id")
            if "snapshot_path" in det:
                event["snapshot_path"] = det.get("snapshot_path")
            if "sensor" in det:
                event["sensor"] = det.get("sensor")

            meta = dict(packet.meta)
            # Intent: output-level idempotency key is derived from stable detection attributes.
            meta["idempotency_key"] = idempotency_key
            meta["source_packet_id"] = packet.packet_id

            out.append(StreamPacket.new(kind="event", source_id=camera_id, payload=event, ts=str(packet.ts), meta=meta))
            self.emitted_total += 1

        return out

    def metrics(self) -> dict[str, int]:
        return {"emitted_total": int(self.emitted_total), "skipped_total": int(self.skipped_total)}

    def close(self) -> None:
        return

