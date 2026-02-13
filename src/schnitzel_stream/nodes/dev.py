from __future__ import annotations

"""
Development-only nodes for the Phase 1 in-proc graph runtime.

Intent:
- Provide minimal source/transform/sink primitives to exercise the v2 runtime in unit tests.
- Keep these nodes dependency-free so they run on almost any edge device.
"""

from typing import Any, Iterable
import json

from schnitzel_stream.packet import StreamPacket


class StaticSource:
    """Emit a finite list of packets from config.

    Config:
    - packets: list[dict]
      - kind: str (default: "raw")
      - source_id: str (default: node_id)
      - payload: any
      - ts: str (optional; ISO-8601)
      - meta: dict (optional)
    """

    OUTPUT_KINDS = {"*"}

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        self._node_id = str(node_id or "source")
        self._config = dict(config or {})

    def run(self) -> Iterable[StreamPacket]:
        packets = self._config.get("packets", [])
        if not isinstance(packets, list):
            raise TypeError("StaticSource config requires 'packets' as a list")

        for idx, item in enumerate(packets):
            if not isinstance(item, dict):
                raise TypeError(f"StaticSource packets[{idx}] must be a mapping")
            kind = str(item.get("kind", "raw"))
            source_id = str(item.get("source_id", self._node_id))
            payload = item.get("payload")

            ts_raw = item.get("ts")
            ts = str(ts_raw) if isinstance(ts_raw, str) and ts_raw.strip() else None

            meta_raw = item.get("meta", {})
            meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}

            yield StreamPacket.new(kind=kind, source_id=source_id, payload=payload, ts=ts, meta=meta)

    def close(self) -> None:
        return


class Identity:
    """Pass-through node (no-op)."""

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}

    def __init__(self, **_kwargs: Any) -> None:
        # Accept config/context kwargs for forward-compatibility with richer runtimes.
        return

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        yield packet

    def close(self) -> None:
        return


class PrintSink:
    """Print each packet as one JSON line (dev-only)."""

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}

    def __init__(self, *, prefix: str | None = None, forward: bool | None = None, **_kwargs: Any) -> None:
        self._prefix = str(prefix or "")
        self._forward = bool(forward or False)

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        data = {
            "packet_id": packet.packet_id,
            "ts": packet.ts,
            "kind": packet.kind,
            "source_id": packet.source_id,
            "payload": packet.payload,
            "meta": packet.meta,
        }
        # Intent:
        # - `payload` may contain arbitrary Python types during migration.
        # - dev sink should never crash just because payload isn't JSON-serializable.
        print(self._prefix + json.dumps(data, default=str), flush=True)
        if self._forward:
            return [packet]
        return []

    def close(self) -> None:
        return


class FooSource:
    """Test-only source that emits a single `kind=foo` packet.

    Intent:
    - Used by static graph compatibility tests to validate kind mismatches.
    """

    OUTPUT_KINDS = {"foo"}

    def __init__(self, **_kwargs: Any) -> None:
        return

    def run(self) -> Iterable[StreamPacket]:
        yield StreamPacket.new(kind="foo", source_id="dev", payload={})

    def close(self) -> None:
        return


class BarSink:
    """Test-only sink that accepts `kind=bar` packets only."""

    INPUT_KINDS = {"bar"}

    def __init__(self, **_kwargs: Any) -> None:
        return

    def process(self, _packet: StreamPacket) -> Iterable[StreamPacket]:
        return []

    def close(self) -> None:
        return
