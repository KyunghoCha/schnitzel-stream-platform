from __future__ import annotations

import pytest

from schnitzel_stream.nodes.durable_sqlite import SqliteQueueAckSink, SqliteQueueSink
from schnitzel_stream.packet import StreamPacket


def _enqueue_packet(db_path) -> None:
    sink = SqliteQueueSink(config={"path": str(db_path)})
    try:
        pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"x": 1}, meta={})
        sink.process(pkt)
    finally:
        sink.close()


def test_sqlite_queue_ack_sink_metrics_for_acked_and_missing_seq(tmp_path):
    db_path = tmp_path / "q.sqlite3"
    _enqueue_packet(db_path)

    ack = SqliteQueueAckSink(config={"path": str(db_path)})
    try:
        ok = StreamPacket.new(kind="event", source_id="cam01", payload={"x": 1}, meta={"durable": {"seq": 1}})
        missing = StreamPacket.new(kind="event", source_id="cam01", payload={"x": 1}, meta={"durable": {"seq": 999}})
        assert list(ack.process(ok)) == []
        assert list(ack.process(missing)) == []

        m = ack.metrics()
        assert m["acked_total"] == 1
        assert m["ack_invalid_total"] == 0
        assert m["ack_missing_total"] == 1
        assert m["queue_depth"] == 0
    finally:
        ack.close()


def test_sqlite_queue_ack_sink_non_positive_seq_counts_invalid(tmp_path):
    db_path = tmp_path / "q.sqlite3"
    _enqueue_packet(db_path)

    ack = SqliteQueueAckSink(config={"path": str(db_path)})
    try:
        invalid = StreamPacket.new(kind="event", source_id="cam01", payload={"x": 1}, meta={"durable": {"seq": 0}})
        assert list(ack.process(invalid)) == []
        m = ack.metrics()
        assert m["acked_total"] == 0
        assert m["ack_invalid_total"] == 1
        assert m["ack_missing_total"] == 0
        assert m["queue_depth"] == 1
    finally:
        ack.close()


def test_sqlite_queue_ack_sink_seq_type_error_still_raises_and_counts_invalid(tmp_path):
    db_path = tmp_path / "q.sqlite3"
    _enqueue_packet(db_path)

    ack = SqliteQueueAckSink(config={"path": str(db_path)})
    try:
        bad = StreamPacket.new(kind="event", source_id="cam01", payload={"x": 1}, meta={"durable": {"seq": "x"}})
        with pytest.raises(ValueError, match="seq as int"):
            ack.process(bad)
        m = ack.metrics()
        assert m["acked_total"] == 0
        assert m["ack_invalid_total"] == 1
        assert m["ack_missing_total"] == 0
        assert m["queue_depth"] == 1
    finally:
        ack.close()
