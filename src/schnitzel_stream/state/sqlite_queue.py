from __future__ import annotations

"""
SQLite-backed durable queue (Phase 2 draft).

Intent:
- Provide a tiny, dependency-free store-and-forward primitive for edge devices.
- Use SQLite WAL mode for reasonable durability/performance tradeoffs.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from schnitzel_stream.packet import StreamPacket


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class QueuedPacket:
    seq: int
    packet: StreamPacket


class SqliteQueue:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Intent:
        # - `check_same_thread=False` to avoid surprising failures if callers use threads later.
        # - Phase 2 still expects single-process access; multi-process concurrency requires more policy.
        self._conn = sqlite3.connect(str(self._path), timeout=30.0, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        self._init_db()

    @property
    def path(self) -> Path:
        return self._path

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        # Intent: prefer durability over throughput by default for store-and-forward.
        cur.execute("PRAGMA synchronous=FULL;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS packets (
              seq INTEGER PRIMARY KEY AUTOINCREMENT,
              enqueued_at TEXT NOT NULL,
              idempotency_key TEXT,
              packet_id TEXT NOT NULL,
              ts TEXT NOT NULL,
              kind TEXT NOT NULL,
              source_id TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              meta_json TEXT NOT NULL
            )
            """
        )
        cols = [r["name"] for r in cur.execute("PRAGMA table_info(packets)").fetchall()]
        if "idempotency_key" not in cols:
            # Backwards-compatible migration from Phase 2 early drafts.
            cur.execute("ALTER TABLE packets ADD COLUMN idempotency_key TEXT")
            cur.execute(
                "UPDATE packets SET idempotency_key = packet_id "
                "WHERE idempotency_key IS NULL OR idempotency_key = ''"
            )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_packets_packet_id ON packets(packet_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_packets_idempotency ON packets(idempotency_key)")
        self._conn.commit()

    def enqueue(self, packet: StreamPacket, *, idempotency_key: str | None = None) -> int:
        key_raw = idempotency_key or packet.meta.get("idempotency_key") or packet.packet_id
        key = str(key_raw).strip()
        if not key:
            raise ValueError("idempotency_key must not be empty")

        # P7.1 portability rule:
        # - Durable lanes are JSON-only until a blob/handle strategy exists.
        # - Do not silently stringify non-serializable objects (it breaks replay correctness).
        try:
            payload_json = json.dumps(packet.payload, separators=(",", ":"))
            meta_json = json.dumps(packet.meta, separators=(",", ":"))
        except TypeError as exc:
            raise TypeError(
                "SqliteQueue requires JSON-serializable packet.payload and packet.meta "
                f"(kind={packet.kind} source_id={packet.source_id})"
            ) from exc
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO packets (
              enqueued_at, idempotency_key, packet_id, ts, kind, source_id, payload_json, meta_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso_utc(),
                key,
                packet.packet_id,
                packet.ts,
                packet.kind,
                packet.source_id,
                payload_json,
                meta_json,
            ),
        )
        self._conn.commit()
        if cur.rowcount == 1:
            seq = cur.lastrowid
            if seq is None:
                raise RuntimeError("sqlite enqueue failed: lastrowid is None")
            return int(seq)

        # Insert was ignored due to idempotency constraint; return existing seq.
        row = cur.execute("SELECT seq FROM packets WHERE idempotency_key = ?", (key,)).fetchone()
        if row is None:
            raise RuntimeError("sqlite enqueue failed: idempotency row not found after conflict")
        return int(row["seq"])

    def read(self, *, limit: int = 100) -> list[QueuedPacket]:
        lim = int(limit)
        if lim <= 0:
            return []

        cur = self._conn.cursor()
        rows = cur.execute(
            """
            SELECT seq, packet_id, ts, kind, source_id, payload_json, meta_json
            FROM packets
            ORDER BY seq ASC
            LIMIT ?
            """,
            (lim,),
        ).fetchall()

        out: list[QueuedPacket] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            meta_raw: Any = json.loads(row["meta_json"])
            meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
            pkt = StreamPacket(
                packet_id=str(row["packet_id"]),
                ts=str(row["ts"]),
                kind=str(row["kind"]),
                source_id=str(row["source_id"]),
                payload=payload,
                meta=meta,
            )
            out.append(QueuedPacket(seq=int(row["seq"]), packet=pkt))
        return out

    def count(self) -> int:
        cur = self._conn.cursor()
        row = cur.execute("SELECT COUNT(*) AS n FROM packets").fetchone()
        if row is None:
            return 0
        return int(row["n"])

    def delete_up_to(self, *, seq: int) -> int:
        s = int(seq)
        if s <= 0:
            return 0
        cur = self._conn.cursor()
        cur.execute("DELETE FROM packets WHERE seq <= ?", (s,))
        self._conn.commit()
        return int(cur.rowcount or 0)

    def ack(self, *, seq: int) -> bool:
        s = int(seq)
        if s <= 0:
            return False
        cur = self._conn.cursor()
        cur.execute("DELETE FROM packets WHERE seq = ?", (s,))
        self._conn.commit()
        return int(cur.rowcount or 0) > 0

    def close(self) -> None:
        try:
            self._conn.close()
        finally:
            return
