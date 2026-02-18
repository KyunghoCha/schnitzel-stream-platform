from __future__ import annotations

"""
Durable queue nodes backed by SQLite (Phase 2 draft).

Intent:
- Provide a minimal store-and-forward building block without external services.
- Keep semantics explicit in config; reliability hardening continues in Phase 2.
"""

from dataclasses import replace
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.state.sqlite_queue import SqliteQueue


class SqliteQueueSink:
    """Persist packets to a SQLite queue (WAL).

    Config:
    - path: str (required) : sqlite file path
    - forward: bool (default: false) : if true, emit the packet downstream after enqueue
    - meta_key: str (default: "durable") : meta key to store enqueue seq/path when forwarding
    """

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True  # JSON-only until a blob/handle strategy exists (P7.1).
    INPUT_PROFILE = "json_portable"
    OUTPUT_PROFILE = "json_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SqliteQueueSink requires config.path (sqlite file path)")

        self._node_id = str(node_id or "queue_sink")
        self._queue = SqliteQueue(path.strip())
        self._forward = bool(cfg.get("forward", False))
        self._meta_key = str(cfg.get("meta_key", "durable"))
        self._enqueued_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        seq = self._queue.enqueue(packet)
        self._enqueued_total += 1
        if not self._forward:
            return []

        meta = dict(packet.meta)
        meta[self._meta_key] = {
            "queue": "sqlite",
            "path": str(self._queue.path),
            "seq": seq,
            "node_id": self._node_id,
        }
        return [replace(packet, meta=meta)]

    def metrics(self) -> dict[str, int]:
        return {
            "enqueued_total": int(self._enqueued_total),
            "queue_depth": int(self._queue.count()),
        }

    def close(self) -> None:
        self._queue.close()


class SqliteQueueSource:
    """Emit queued packets from SQLite.

    Config:
    - path: str (required) : sqlite file path
    - limit: int (default: 100) : max packets to emit per run
    - delete_on_emit: bool (default: false) : delete rows after emitting a batch (unsafe without end-to-end ack)
    - meta_key: str (default: "durable") : meta key to attach seq/path to emitted packets
    """

    OUTPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True  # Emitted packets remain portable (JSON/ref-safe) only.
    # Intent:
    # - Queue rows can contain plain JSON events or portable references (e.g., bytes_ref).
    # - `ref_portable` keeps JSON consumers compatible while allowing explicit ref consumers.
    OUTPUT_PROFILE = "ref_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SqliteQueueSource requires config.path (sqlite file path)")

        self._node_id = str(node_id or "queue_source")
        self._queue = SqliteQueue(path.strip())
        self._limit = int(cfg.get("limit", 100))
        self._delete_on_emit = bool(cfg.get("delete_on_emit", False))
        self._meta_key = str(cfg.get("meta_key", "durable"))
        self._emitted_total = 0

    def run(self) -> Iterable[StreamPacket]:
        batch = self._queue.read(limit=self._limit)
        if not batch:
            return []

        out: list[StreamPacket] = []
        for row in batch:
            meta = dict(row.packet.meta)
            meta[self._meta_key] = {
                "queue": "sqlite",
                "path": str(self._queue.path),
                "seq": row.seq,
                "node_id": self._node_id,
            }
            out.append(replace(row.packet, meta=meta))

        self._emitted_total += len(out)

        if self._delete_on_emit:
            # Intent: delete-on-emit is a dev-only shortcut; it is not safe without downstream ack semantics.
            self._queue.delete_up_to(seq=batch[-1].seq)

        return out

    def metrics(self) -> dict[str, int]:
        return {
            "emitted_total": int(self._emitted_total),
            "queue_depth": int(self._queue.count()),
        }

    def close(self) -> None:
        self._queue.close()


class SqliteQueueAckSink:
    """Acknowledge (delete) queued rows after successful downstream processing.

    Config:
    - path: str (required) : sqlite file path
    - meta_key: str (default: "durable") : meta key containing {"seq": int}
    - forward: bool (default: false) : if true, emit the packet after ack
    """

    INPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True  # Ack lane assumes JSON-only packets (P7.1).
    INPUT_PROFILE = "json_portable"
    OUTPUT_PROFILE = "json_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SqliteQueueAckSink requires config.path (sqlite file path)")

        self._node_id = str(node_id or "queue_ack")
        self._queue = SqliteQueue(path.strip())
        self._meta_key = str(cfg.get("meta_key", "durable"))
        self._forward = bool(cfg.get("forward", False))
        self._acked_total = 0
        self._ack_invalid_total = 0
        self._ack_missing_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        meta = dict(packet.meta)
        raw = meta.get(self._meta_key, {})
        if not isinstance(raw, dict):
            raise ValueError(f"SqliteQueueAckSink expects packet.meta[{self._meta_key}] as a mapping")
        seq = raw.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool):
            self._ack_invalid_total += 1
            raise ValueError(f"SqliteQueueAckSink expects packet.meta[{self._meta_key}].seq as int")
        if seq <= 0:
            # Intent: treat non-positive seq as invalid ack input while keeping compatibility (no exception for value).
            self._ack_invalid_total += 1
        elif self._queue.ack(seq=seq):
            self._acked_total += 1
        else:
            self._ack_missing_total += 1
        if self._forward:
            return [packet]
        return []

    def metrics(self) -> dict[str, int]:
        return {
            "acked_total": int(self._acked_total),
            "ack_invalid_total": int(self._ack_invalid_total),
            "ack_missing_total": int(self._ack_missing_total),
            "queue_depth": int(self._queue.count()),
        }

    def close(self) -> None:
        self._queue.close()
