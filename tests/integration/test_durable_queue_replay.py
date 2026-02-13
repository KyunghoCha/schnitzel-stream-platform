from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner
from schnitzel_stream.state.sqlite_queue import SqliteQueue


def test_durable_queue_replay_and_ack_across_restarts(tmp_path):
    db_path = tmp_path / "queue.sqlite3"

    # 1) Enqueue (twice) with a stable idempotency key -> should store only once.
    enqueue_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {
                        "kind": "event",
                        "source_id": "cam01",
                        "payload": {"x": 1},
                        "meta": {"idempotency_key": "event-0001"},
                    }
                ]
            },
        ),
        NodeSpec(
            node_id="q",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink",
            config={"path": str(db_path), "forward": False},
        ),
    ]
    enqueue_edges = [EdgeSpec(src="src", dst="q")]

    runner = InProcGraphRunner()
    runner.run(nodes=enqueue_nodes, edges=enqueue_edges)
    runner.run(nodes=enqueue_nodes, edges=enqueue_edges)

    q = SqliteQueue(db_path)
    try:
        assert len(q.read(limit=10)) == 1
    finally:
        q.close()

    # 2) Drain + ack in a separate run (restart): queue should become empty.
    drain_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": 100, "delete_on_emit": False},
        ),
        NodeSpec(node_id="op", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(
            node_id="ack",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueAckSink",
            config={"path": str(db_path)},
        ),
    ]
    drain_edges = [EdgeSpec(src="src", dst="op"), EdgeSpec(src="op", dst="ack")]

    runner2 = InProcGraphRunner()
    result = runner2.run(nodes=drain_nodes, edges=drain_edges)
    assert len(result.outputs_by_node["src"]) == 1

    q2 = SqliteQueue(db_path)
    try:
        assert q2.read(limit=10) == []
    finally:
        q2.close()

    # 3) Second drain should be a no-op.
    runner3 = InProcGraphRunner()
    result2 = runner3.run(nodes=drain_nodes, edges=drain_edges)
    assert len(result2.outputs_by_node["src"]) == 0

