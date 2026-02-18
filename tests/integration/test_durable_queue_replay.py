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

    q3 = SqliteQueue(db_path)
    try:
        assert q3.ack(seq=0) is False
        assert q3.ack(seq=-1) is False
        assert q3.read(limit=10) == []
    finally:
        q3.close()


def test_durable_queue_delete_on_emit_clears_rows_without_ack(tmp_path):
    db_path = tmp_path / "queue.sqlite3"

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
                        "meta": {"idempotency_key": "event-delete-on-emit"},
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
    InProcGraphRunner().run(nodes=enqueue_nodes, edges=enqueue_edges)

    drain_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": 100, "delete_on_emit": True},
        ),
        NodeSpec(node_id="out", kind="sink", plugin="schnitzel_stream.nodes.dev:PrintSink", config={"prefix": "T "}),
    ]
    drain_edges = [EdgeSpec(src="src", dst="out")]
    result = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    assert len(result.outputs_by_node["src"]) == 1

    q = SqliteQueue(db_path)
    try:
        assert q.read(limit=10) == []
    finally:
        q.close()


def test_durable_queue_partial_ack_replays_only_remaining_packets(tmp_path):
    db_path = tmp_path / "queue.sqlite3"

    packets = []
    for idx in range(5):
        packets.append(
            {
                "kind": "event",
                "source_id": "cam01",
                "payload": {"x": idx},
                "meta": {"idempotency_key": f"event-{idx:03d}"},
            }
        )
    enqueue_nodes = [
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
    InProcGraphRunner().run(nodes=enqueue_nodes, edges=[EdgeSpec(src="src", dst="q")])

    drain_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": 2, "delete_on_emit": False},
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

    r1 = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    assert len(r1.outputs_by_node["src"]) == 2

    q1 = SqliteQueue(db_path)
    try:
        assert len(q1.read(limit=10)) == 3
    finally:
        q1.close()

    drain_nodes[0] = NodeSpec(
        node_id="src",
        kind="source",
        plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
        config={"path": str(db_path), "limit": 10, "delete_on_emit": False},
    )
    r2 = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    assert len(r2.outputs_by_node["src"]) == 3

    r3 = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    assert len(r3.outputs_by_node["src"]) == 0
