from __future__ import annotations

import pytest

from schnitzel_stream.graph.compat import GraphCompatibilityError, validate_graph_compat
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec


def test_validate_graph_compat_rejects_sink_with_outgoing_edges():
    nodes = [
        NodeSpec(node_id="a", kind="sink", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(node_id="b", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
    ]
    edges = [EdgeSpec(src="a", dst="b")]
    with pytest.raises(GraphCompatibilityError, match="sink node must not have outgoing edges"):
        validate_graph_compat(nodes, edges)


def test_validate_graph_compat_rejects_plugin_missing_process():
    nodes = [NodeSpec(node_id="n1", kind="node", plugin="schnitzel_stream.packet:StreamPacket")]
    with pytest.raises(GraphCompatibilityError, match="implement process"):
        validate_graph_compat(nodes, edges=[])


def test_validate_graph_compat_rejects_packet_kind_mismatch():
    nodes = [
        NodeSpec(node_id="src", kind="source", plugin="schnitzel_stream.nodes.dev:FooSource"),
        NodeSpec(node_id="sink", kind="sink", plugin="schnitzel_stream.nodes.dev:BarSink"),
    ]
    edges = [EdgeSpec(src="src", dst="sink")]
    with pytest.raises(GraphCompatibilityError, match="packet kind mismatch"):
        validate_graph_compat(nodes, edges)

