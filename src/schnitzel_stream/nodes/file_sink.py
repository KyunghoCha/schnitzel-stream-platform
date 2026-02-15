from __future__ import annotations

"""
JSONL / file sink node plugins.

Intent:
- Provide lightweight local sinks for edge and dev lanes without relying on legacy emitters.
- Keep output shape explicit (`payload` vs `packet`) and portable (JSON).
"""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket


def _build_record(packet: StreamPacket, *, body_mode: str) -> Any:
    if body_mode == "packet":
        return {
            "packet_id": packet.packet_id,
            "ts": packet.ts,
            "kind": packet.kind,
            "source_id": packet.source_id,
            "payload": packet.payload,
            "meta": dict(packet.meta),
        }
    return packet.payload


class JsonlSink:
    """Append one JSON object per line.

    Config:
    - path: str (required)
    - body: "payload"|"packet" (default: "packet")
    - forward: bool (default: false)
    - ensure_ascii: bool (default: false)
    - flush: bool (default: true)
    """

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})

        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("JsonlSink requires config.path")

        body_mode = str(cfg.get("body", "packet")).strip().lower() or "packet"
        if body_mode not in ("payload", "packet"):
            raise ValueError("JsonlSink config.body must be 'payload' or 'packet'")

        self._node_id = str(node_id or "jsonl_sink")
        self._path = Path(path.strip())
        self._path.parent.mkdir(parents=True, exist_ok=True)

        self._body_mode = body_mode
        self._forward = bool(cfg.get("forward", False))
        self._ensure_ascii = bool(cfg.get("ensure_ascii", False))
        self._flush = bool(cfg.get("flush", True))

        self._fh = self._path.open("a", encoding="utf-8")
        self._written_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        rec = _build_record(packet, body_mode=self._body_mode)
        try:
            line = json.dumps(rec, ensure_ascii=self._ensure_ascii)
        except TypeError as exc:
            raise TypeError(f"{self._node_id}: payload is not JSON-serializable") from exc

        self._fh.write(line + "\n")
        if self._flush:
            self._fh.flush()

        self._written_total += 1
        if not self._forward:
            return []
        return [packet]

    def metrics(self) -> dict[str, int]:
        return {"written_total": int(self._written_total)}

    def close(self) -> None:
        fh = getattr(self, "_fh", None)
        if fh is not None:
            fh.close()


class JsonFileSink:
    """Write one JSON file per packet.

    Config:
    - dir: str (default: "outputs/packets")
    - filename_template: str (default: "{seq:06d}_{source_id}_{kind}.json")
      - fields: seq, packet_id, source_id, kind, ts
    - body: "payload"|"packet" (default: "payload")
    - forward: bool (default: false)
    - ensure_ascii: bool (default: false)
    - indent: int (default: 2)
    - meta_key: str (default: "file")
    """

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})

        out_dir = str(cfg.get("dir", "outputs/packets")).strip() or "outputs/packets"
        body_mode = str(cfg.get("body", "payload")).strip().lower() or "payload"
        if body_mode not in ("payload", "packet"):
            raise ValueError("JsonFileSink config.body must be 'payload' or 'packet'")

        self._node_id = str(node_id or "json_file_sink")
        self._dir = Path(out_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._filename_template = str(cfg.get("filename_template", "{seq:06d}_{source_id}_{kind}.json"))
        self._body_mode = body_mode
        self._forward = bool(cfg.get("forward", False))
        self._ensure_ascii = bool(cfg.get("ensure_ascii", False))
        self._indent = int(cfg.get("indent", 2))
        self._meta_key = str(cfg.get("meta_key", "file"))

        self._written_total = 0

    def _filename_for_packet(self, packet: StreamPacket) -> str:
        safe_ts = str(packet.ts).replace(":", "-")
        raw = self._filename_template.format(
            seq=int(self._written_total),
            packet_id=packet.packet_id,
            source_id=packet.source_id,
            kind=packet.kind,
            ts=safe_ts,
        )

        # Intent: block template-based path traversal; sink writes under config.dir only.
        base = Path(raw).name
        if not base:
            raise ValueError("JsonFileSink resolved empty filename")
        return base

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        rec = _build_record(packet, body_mode=self._body_mode)

        filename = self._filename_for_packet(packet)
        path = self._dir / filename

        try:
            text = json.dumps(rec, ensure_ascii=self._ensure_ascii, indent=self._indent)
        except TypeError as exc:
            raise TypeError(f"{self._node_id}: payload is not JSON-serializable") from exc

        path.write_text(text + "\n", encoding="utf-8")
        self._written_total += 1

        if not self._forward:
            return []

        meta = dict(packet.meta)
        meta[self._meta_key] = {
            "path": str(path),
            "node_id": self._node_id,
        }
        return [replace(packet, meta=meta)]

    def metrics(self) -> dict[str, int]:
        return {"written_total": int(self._written_total)}

    def close(self) -> None:
        return
