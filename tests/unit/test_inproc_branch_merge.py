from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_inproc_runtime_fanout_to_multiple_sinks():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "demo", "source_id": "s", "payload": {"n": 1}},
                    {"kind": "demo", "source_id": "s", "payload": {"n": 2}},
                ]
            },
        ),
        NodeSpec(node_id="fanout", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="sink1", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="sink2", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [
        EdgeSpec(src="src", dst="fanout"),
        EdgeSpec(src="fanout", dst="sink1"),
        EdgeSpec(src="fanout", dst="sink2"),
    ]

    runner = InProcGraphRunner()
    result = runner.run(nodes=nodes, edges=edges)

    assert len(result.outputs_by_node["sink1"]) == 2
    assert len(result.outputs_by_node["sink2"]) == 2


def test_inproc_runtime_merges_multiple_sources_into_one_node_deterministically():
    nodes = [
        NodeSpec(
            node_id="a",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": [{"kind": "demo", "source_id": "a", "payload": {"id": "a1"}}]},
        ),
        NodeSpec(
            node_id="b",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": [{"kind": "demo", "source_id": "b", "payload": {"id": "b1"}}]},
        ),
        NodeSpec(node_id="merge", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="out", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [
        EdgeSpec(src="a", dst="merge"),
        EdgeSpec(src="b", dst="merge"),
        EdgeSpec(src="merge", dst="out"),
    ]

    runner = InProcGraphRunner()
    result = runner.run(nodes=nodes, edges=edges)

    outs = result.outputs_by_node["out"]
    assert [p.payload["id"] for p in outs] == ["a1", "b1"]


def test_inproc_runtime_interleaves_multiple_sources_round_robin():
    nodes = [
        NodeSpec(
            node_id="a",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "demo", "source_id": "a", "payload": {"id": "a1"}},
                    {"kind": "demo", "source_id": "a", "payload": {"id": "a2"}},
                ]
            },
        ),
        NodeSpec(
            node_id="b",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "demo", "source_id": "b", "payload": {"id": "b1"}},
                    {"kind": "demo", "source_id": "b", "payload": {"id": "b2"}},
                ]
            },
        ),
        NodeSpec(node_id="merge", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="out", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [
        EdgeSpec(src="a", dst="merge"),
        EdgeSpec(src="b", dst="merge"),
        EdgeSpec(src="merge", dst="out"),
    ]

    runner = InProcGraphRunner()
    result = runner.run(nodes=nodes, edges=edges)

    outs = result.outputs_by_node["out"]
    assert [p.payload["id"] for p in outs] == ["a1", "b1", "a2", "b2"]
