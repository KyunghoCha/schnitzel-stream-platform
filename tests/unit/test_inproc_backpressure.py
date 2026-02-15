from __future__ import annotations

import pytest

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import GraphExecutionError, InProcGraphRunner


def test_inproc_runner_drops_packets_on_inbox_overflow():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": [{"kind": "k", "source_id": "s", "payload": {"x": 1}}]},
        ),
        NodeSpec(
            node_id="burst",
            kind="node",
            plugin="schnitzel_stream.nodes.dev:BurstNode",
            config={"count": 5},
        ),
        NodeSpec(
            node_id="sink",
            kind="sink",
            plugin="schnitzel_stream.nodes.dev:Identity",
            config={"__runtime__": {"inbox_max": 2, "inbox_overflow": "drop_new"}},
        ),
    ]
    edges = [
        EdgeSpec(src="src", dst="burst"),
        EdgeSpec(src="burst", dst="sink"),
    ]

    result = InProcGraphRunner().run(nodes=nodes, edges=edges)
    assert len(result.outputs_by_node["sink"]) == 2
    assert result.metrics["packets.dropped_total"] == 3
    assert result.metrics["node.sink.inbox_dropped_total"] == 3


def test_inproc_runner_can_fail_closed_on_inbox_overflow():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": [{"kind": "k", "source_id": "s", "payload": {"x": 1}}]},
        ),
        NodeSpec(
            node_id="burst",
            kind="node",
            plugin="schnitzel_stream.nodes.dev:BurstNode",
            config={"count": 5},
        ),
        NodeSpec(
            node_id="sink",
            kind="sink",
            plugin="schnitzel_stream.nodes.dev:Identity",
            config={"__runtime__": {"inbox_max": 2, "inbox_overflow": "error"}},
        ),
    ]
    edges = [
        EdgeSpec(src="src", dst="burst"),
        EdgeSpec(src="burst", dst="sink"),
    ]

    with pytest.raises(GraphExecutionError):
        InProcGraphRunner().run(nodes=nodes, edges=edges)

