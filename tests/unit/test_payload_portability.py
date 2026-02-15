from __future__ import annotations

import pytest

from schnitzel_stream.graph.compat import GraphCompatibilityError, validate_graph_compat
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_graph_compat_rejects_frame_into_durable_queue_lane():
    nodes = [
        NodeSpec(
            node_id="frames",
            kind="source",
            plugin="schnitzel_stream.packs.vision.nodes.video:OpenCvVideoFileSource",
            config={},
        ),
        NodeSpec(
            node_id="q",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink",
            config={"path": "outputs/queues/dev_test.sqlite3", "forward": False},
        ),
    ]
    edges = [EdgeSpec(src="frames", dst="q")]

    with pytest.raises(GraphCompatibilityError):
        validate_graph_compat(nodes, edges, transport="inproc")


def test_durable_queue_rejects_non_json_payload_at_runtime(tmp_path):
    db_path = tmp_path / "events.sqlite3"

    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "event", "source_id": "cam01", "payload": {"bad": object()}, "meta": {"idempotency_key": "e1"}}
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
    edges = [EdgeSpec(src="src", dst="q")]

    with pytest.raises(TypeError):
        InProcGraphRunner().run(nodes=nodes, edges=edges)

