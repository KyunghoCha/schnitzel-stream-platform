from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_bytes_file_ref_roundtrip_through_durable_queue(tmp_path):
    blob_dir = tmp_path / "blobs"
    db_path = tmp_path / "queue.sqlite3"

    enqueue_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "bytes", "source_id": "demo01", "payload": b"hello", "meta": {"idempotency_key": "b1"}}
                ]
            },
        ),
        NodeSpec(
            node_id="to_ref",
            kind="node",
            plugin="schnitzel_stream.nodes.blob_ref:BytesToFileRefNode",
            config={"dir": str(blob_dir), "compute_sha256": True},
        ),
        NodeSpec(
            node_id="q",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink",
            config={"path": str(db_path), "forward": False},
        ),
    ]
    enqueue_edges = [
        EdgeSpec(src="src", dst="to_ref"),
        EdgeSpec(src="to_ref", dst="q"),
    ]

    InProcGraphRunner().run(nodes=enqueue_nodes, edges=enqueue_edges)

    drain_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": 10, "delete_on_emit": False},
        ),
        NodeSpec(
            node_id="to_bytes",
            kind="node",
            plugin="schnitzel_stream.nodes.blob_ref:FileRefToBytesNode",
            config={"output_kind": "bytes"},
        ),
        NodeSpec(node_id="out", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    drain_edges = [
        EdgeSpec(src="src", dst="to_bytes"),
        EdgeSpec(src="to_bytes", dst="out"),
    ]

    result = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    outs = result.outputs_by_node["out"]
    assert len(outs) == 1
    assert outs[0].payload == b"hello"

