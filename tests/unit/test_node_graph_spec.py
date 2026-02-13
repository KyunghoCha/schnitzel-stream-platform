from __future__ import annotations

import textwrap

import pytest

from schnitzel_stream.graph.spec import load_node_graph_spec
from schnitzel_stream.graph.validate import validate_graph


def test_load_node_graph_spec_parses_nodes_and_edges(tmp_path):
    p = tmp_path / "graph.yaml"
    p.write_text(
        textwrap.dedent(
            """
            version: 2
            nodes:
              - id: a
                kind: source
                plugin: my.nodes:Source
              - id: b
                plugin: my.nodes:Op
            edges:
              - from: a
                to: b
            """
        ).lstrip(),
        encoding="utf-8",
    )

    spec = load_node_graph_spec(p)
    assert spec.version == 2
    assert [n.node_id for n in spec.nodes] == ["a", "b"]
    assert [(e.src, e.dst) for e in spec.edges] == [("a", "b")]

    # Topology validation is separate from parsing.
    validate_graph(spec.nodes, spec.edges)


def test_load_node_graph_spec_rejects_wrong_version(tmp_path):
    p = tmp_path / "graph.yaml"
    p.write_text("version: 1\nnodes: []\nedges: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="version must be 2"):
        load_node_graph_spec(p)

