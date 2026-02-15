from __future__ import annotations

import pytest

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.graph.validate import GraphValidationError, find_cycle, validate_graph


def test_validate_graph_ok_for_simple_chain():
    nodes = [
        NodeSpec(node_id="a", plugin="x:NodeA"),
        NodeSpec(node_id="b", plugin="x:NodeB"),
        NodeSpec(node_id="c", plugin="x:NodeC"),
    ]
    edges = [
        EdgeSpec(src="a", dst="b"),
        EdgeSpec(src="b", dst="c"),
    ]
    assert find_cycle(nodes, edges) is None
    validate_graph(nodes, edges)


def test_validate_graph_rejects_duplicate_node_ids():
    nodes = [
        NodeSpec(node_id="a", plugin="x:NodeA"),
        NodeSpec(node_id="a", plugin="x:NodeA2"),
    ]
    with pytest.raises(GraphValidationError, match="duplicate node_id"):
        validate_graph(nodes, [])


def test_validate_graph_rejects_edges_to_unknown_nodes():
    nodes = [
        NodeSpec(node_id="a", plugin="x:NodeA"),
    ]
    edges = [EdgeSpec(src="a", dst="missing")]
    with pytest.raises(GraphValidationError, match="dst node not found"):
        validate_graph(nodes, edges)


def test_find_cycle_detects_simple_cycle():
    nodes = [
        NodeSpec(node_id="a", plugin="x:NodeA"),
        NodeSpec(node_id="b", plugin="x:NodeB"),
    ]
    edges = [
        EdgeSpec(src="a", dst="b"),
        EdgeSpec(src="b", dst="a"),
    ]
    cycle = find_cycle(nodes, edges)
    assert cycle is not None
    assert cycle[0] == cycle[-1]

    with pytest.raises(GraphValidationError, match="cycle"):
        validate_graph(nodes, edges, allow_cycles=False)


def test_validate_graph_restricted_cycles_requires_delay_node():
    nodes = [
        NodeSpec(node_id="a", plugin="x:NodeA"),
        NodeSpec(node_id="b", plugin="x:NodeB"),
    ]
    edges = [
        EdgeSpec(src="a", dst="b"),
        EdgeSpec(src="b", dst="a"),
    ]
    with pytest.raises(GraphValidationError, match="without a Delay node"):
        validate_graph(nodes, edges, allow_cycles=True)


def test_validate_graph_restricted_cycles_allows_delay_node():
    nodes = [
        NodeSpec(node_id="a", kind="delay", plugin="x:Delay"),
        NodeSpec(node_id="b", plugin="x:NodeB"),
    ]
    edges = [
        EdgeSpec(src="a", dst="b"),
        EdgeSpec(src="b", dst="a"),
    ]
    assert find_cycle(nodes, edges) is not None
    validate_graph(nodes, edges, allow_cycles=True)
