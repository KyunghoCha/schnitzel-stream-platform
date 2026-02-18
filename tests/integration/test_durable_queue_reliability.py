from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner
from schnitzel_stream.state.sqlite_queue import SqliteQueue


def _enqueue_backlog(*, db_path, count: int) -> None:
    packets = []
    for idx in range(int(count)):
        packets.append(
            {
                "kind": "event",
                "source_id": "cam01",
                "payload": {"x": idx},
                "meta": {"idempotency_key": f"event-{idx:04d}"},
            }
        )
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": packets},
        ),
        NodeSpec(
            node_id="q",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink",
            config={"path": str(db_path), "forward": False},
        ),
    ]
    edges = [EdgeSpec(src="src", dst="q")]
    InProcGraphRunner().run(nodes=nodes, edges=edges)


def _drain_with_ack(*, db_path, limit: int) -> int:
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": int(limit), "delete_on_emit": False},
        ),
        NodeSpec(node_id="op", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(
            node_id="ack",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueAckSink",
            config={"path": str(db_path)},
        ),
    ]
    edges = [EdgeSpec(src="src", dst="op"), EdgeSpec(src="op", dst="ack")]
    result = InProcGraphRunner().run(nodes=nodes, edges=edges)
    return int(len(result.outputs_by_node["src"]))


def test_durable_backlog_chunked_drain_eventually_empties_queue(tmp_path):
    db_path = tmp_path / "queue.sqlite3"
    _enqueue_backlog(db_path=db_path, count=125)

    emitted_total = 0
    rounds = 0
    while True:
        emitted = _drain_with_ack(db_path=db_path, limit=20)
        rounds += 1
        emitted_total += emitted
        if emitted == 0:
            break

    assert rounds > 1
    assert emitted_total == 125

    q = SqliteQueue(db_path)
    try:
        assert q.count() == 0
    finally:
        q.close()
