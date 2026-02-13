from __future__ import annotations

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.state.sqlite_queue import SqliteQueue


def test_sqlite_queue_roundtrip(tmp_path):
    q = SqliteQueue(tmp_path / "q.sqlite3")
    try:
        pkt = StreamPacket.new(kind="demo", source_id="cam01", payload={"x": 1}, meta={"k": "v"})
        seq = q.enqueue(pkt)

        rows = q.read(limit=10)
        assert len(rows) == 1
        assert rows[0].seq == seq
        assert rows[0].packet.kind == "demo"
        assert rows[0].packet.source_id == "cam01"
        assert rows[0].packet.payload == {"x": 1}
        assert rows[0].packet.meta == {"k": "v"}

        deleted = q.delete_up_to(seq=seq)
        assert deleted == 1
        assert q.read(limit=10) == []
    finally:
        q.close()

