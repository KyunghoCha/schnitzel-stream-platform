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

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("SqliteQueueSink requires config.path (sqlite file path)")

        self._node_id = str(node_id or "queue_sink")
        self._queue = SqliteQueue(path.strip())
        self._forward = bool(cfg.get("forward", False))
        self._meta_key = str(cfg.get("meta_key", "durable"))

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        seq = self._queue.enqueue(packet)
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

        if self._delete_on_emit:
            # Intent: delete-on-emit is a dev-only shortcut; it is not safe without downstream ack semantics.
            self._queue.delete_up_to(seq=batch[-1].seq)

        return out

    def close(self) -> None:
        self._queue.close()
