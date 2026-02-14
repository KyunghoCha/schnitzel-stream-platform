from __future__ import annotations

"""
Policy nodes for the v2 node graph runtime.

Intent:
- Phase 4 legacy removal: provide platform-owned equivalents of legacy `ai.rules.*`.
- Keep node contracts explicit via `INPUT_KINDS`/`OUTPUT_KINDS` so graph validation can reject bad wiring.
"""

from dataclasses import replace
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.policy.dedup import DedupController
from schnitzel_stream.policy.zones import ZoneEvaluator, evaluate_zones


class ZonePolicyNode:
    """Attach `payload.zone` based on bbox + configured zones.

    Input payload (packet.kind == "event") expects:
    - event_type: str
    - bbox: {x1,y1,x2,y2}

    Config (one of):
    - zones: list[dict] (inline zones)
      - {zone_id, enabled, polygon}
    - source: "file"|"api"
    - site_id: str (api/file mode)
    - camera_id: str (api/file mode)
    - rule_map: dict[str,str] (default: {})
    - file_path: str (file mode)
    - api_cfg: dict (api mode)
    - cache_ttl_sec: float (default: 30)
    """

    INPUT_KINDS = {"event"}
    OUTPUT_KINDS = {"event"}

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "zone_policy")

        rule_map_raw = cfg.get("rule_map", {})
        self._rule_map = dict(rule_map_raw) if isinstance(rule_map_raw, dict) else {}

        zones_inline = cfg.get("zones")
        self._zones_inline = list(zones_inline) if isinstance(zones_inline, list) else None

        source = str(cfg.get("source", "")).strip()
        if self._zones_inline is not None:
            self._evaluator = None
            self._source = "inline"
        elif source in ("file", "api"):
            self._source = source
            self._evaluator = ZoneEvaluator(
                source=source,
                site_id=str(cfg.get("site_id", "")),
                camera_id=str(cfg.get("camera_id", "")),
                rule_map=self._rule_map,
                api_cfg=dict(cfg.get("api_cfg", {}) or {}) if isinstance(cfg.get("api_cfg", {}), dict) else None,
                file_path=str(cfg.get("file_path", "")) or None,
                cache_ttl_sec=float(cfg.get("cache_ttl_sec", 30.0)),
            )
        else:
            # No zones configured; produce default empty zone results.
            self._source = "none"
            self._evaluator = None

        self._processed_total = 0
        self._inside_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        self._processed_total += 1

        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self._node_id}: expected event payload as a mapping")

        payload = dict(packet.payload)

        if self._zones_inline is not None:
            event_type = str(payload.get("event_type", ""))
            bbox = payload.get("bbox", {})
            bbox_dict = dict(bbox) if isinstance(bbox, dict) else {}
            payload["zone"] = evaluate_zones(event_type, bbox_dict, self._zones_inline, self._rule_map)
        elif self._evaluator is not None:
            payload = self._evaluator.apply(payload)
        else:
            payload["zone"] = {"zone_id": "", "inside": False}

        zone = payload.get("zone", {})
        if isinstance(zone, dict) and bool(zone.get("inside")):
            self._inside_total += 1

        yield replace(packet, payload=payload)

    def metrics(self) -> dict[str, int]:
        return {"processed_total": int(self._processed_total), "inside_total": int(self._inside_total)}

    def close(self) -> None:
        return


class DedupPolicyNode:
    """Drop duplicated event packets based on camera_id/event_type/track_id cooldown policy.

    Config:
    - cooldown_sec: float (default: 10)
    - prune_interval: int (default: 100)
    """

    INPUT_KINDS = {"event"}
    OUTPUT_KINDS = {"event"}

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "dedup_policy")
        self._ctrl = DedupController(
            cooldown_sec=float(cfg.get("cooldown_sec", 10.0)),
            prune_interval=int(cfg.get("prune_interval", 100)),
        )
        self._accepted_total = 0
        self._dropped_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self._node_id}: expected event payload as a mapping")

        if self._ctrl.allow_emit(packet.payload):
            self._accepted_total += 1
            return [packet]

        self._dropped_total += 1
        return []

    def metrics(self) -> dict[str, int]:
        return {"accepted_total": int(self._accepted_total), "dropped_total": int(self._dropped_total)}

    def close(self) -> None:
        return

