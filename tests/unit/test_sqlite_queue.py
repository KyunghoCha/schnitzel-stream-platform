from __future__ import annotations

import pytest

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.state.sqlite_queue import SqliteQueue


def test_sqlite_queue_roundtrip(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={"k": "v"})
        seq = q.enqueue(pkt)
        assert q.enqueue(pkt) == seq  # idempotency_key defaults to packet_id

        rows = q.read(limit=10)
        assert len(rows) == 1
        assert rows[0].seq == seq
        assert rows[0].packet.kind == "demo"
        assert rows[0].packet.source_id == "cam01"
        assert rows[0].packet.payload == {"x": 1}
        assert rows[0].packet.meta == {"k": "v"}

        assert q.ack(seq=seq) is True
        assert q.read(limit=10) == []
    finally:
        q.close()


def test_sqlite_queue_ack_invalid_seq_is_noop(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={})
        q.enqueue(pkt)
        assert q.ack(seq=0) is False
        assert q.ack(seq=-5) is False
        assert len(q.read(limit=10)) == 1
    finally:
        q.close()


def test_sqlite_queue_rejects_blank_idempotency_key(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(
            kind="demo",
            source_id="cam01",
            payload={"x": 1},
            meta={"idempotency_key": "   "},
        )
        with pytest.raises(ValueError, match="idempotency_key.*path=.*kind=demo.*source_id=cam01"):
            q.enqueue(pkt)
    finally:
        q.close()


def test_sqlite_queue_read_non_positive_limit_returns_empty(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={})
        q.enqueue(pkt)
        assert q.read(limit=0) == []
        assert q.read(limit=-3) == []
    finally:
        q.close()


def test_sqlite_queue_delete_up_to_invalid_seq_is_noop(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={})
        q.enqueue(pkt)
        assert q.delete_up_to(seq=0) == 0
        assert q.delete_up_to(seq=-1) == 0
        assert q.count() == 1
    finally:
        q.close()


def test_sqlite_queue_none_idempotency_falls_back_to_packet_id(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={})
        seq1 = q.enqueue(pkt, idempotency_key=None)
        seq2 = q.enqueue(pkt, idempotency_key=None)
        assert seq1 == seq2
        assert q.count() == 1
    finally:
        q.close()


def test_sqlite_queue_serialization_error_includes_context(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(
            kind="demo",
            source_id="cam01",
            payload={"bad": object()},
            meta={},
        )
        with pytest.raises(TypeError, match="path=.*kind=demo.*source_id=cam01"):
            q.enqueue(pkt)
    finally:
        q.close()
