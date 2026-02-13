from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_inproc_graph_runner_executes_simple_dag():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": [{"kind": "test", "source_id": "cam01", "payload": {"x": 1}}]},
        ),
        NodeSpec(node_id="op", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="sink", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [
        EdgeSpec(src="src", dst="op"),
        EdgeSpec(src="op", dst="sink"),
    ]

    result = InProcGraphRunner().run(nodes=nodes, edges=edges)

    assert [p.kind for p in result.outputs_by_node["src"]] == ["test"]
    assert [p.payload for p in result.outputs_by_node["sink"]] == [{"x": 1}]
