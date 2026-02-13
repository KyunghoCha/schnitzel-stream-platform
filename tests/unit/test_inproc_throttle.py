from __future__ import annotations

from schnitzel_stream.control.throttle import FixedBudgetThrottle
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_inproc_runner_throttle_caps_source_emits():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "k", "source_id": "s", "payload": {"i": 0}},
                    {"kind": "k", "source_id": "s", "payload": {"i": 1}},
                    {"kind": "k", "source_id": "s", "payload": {"i": 2}},
                ]
            },
        ),
        NodeSpec(node_id="sink", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [EdgeSpec(src="src", dst="sink")]

    runner = InProcGraphRunner()
    result = runner.run(nodes=nodes, edges=edges, throttle=FixedBudgetThrottle(max_source_emits_total=2))

    assert len(result.outputs_by_node["sink"]) == 2
    assert result.metrics["packets.source_emitted_total"] == 2

