from __future__ import annotations

from pathlib import Path

import pytest

from schnitzel_stream.ops import graph_editor as editor_ops


def test_parse_graph_spec_input_accepts_alias_fields():
    nodes, edges, config = editor_ops.parse_graph_spec_input(
        {
            "version": 2,
            "nodes": [
                {
                    "id": "src",
                    "kind": "source",
                    "plugin": "schnitzel_stream.nodes.dev:StaticSource",
                    "config": {"packets": []},
                },
                {
                    "node_id": "out",
                    "kind": "sink",
                    "plugin": "schnitzel_stream.nodes.dev:PrintSink",
                    "config": {},
                },
            ],
            "edges": [
                {"from": "src", "to": "out"},
            ],
            "config": {"throttle": {"max_queue": 8}},
        }
    )
    assert len(nodes) == 2
    assert nodes[1].node_id == "out"
    assert len(edges) == 1
    assert edges[0].src == "src"
    assert edges[0].dst == "out"
    assert config["throttle"]["max_queue"] == 8


def test_parse_graph_spec_input_rejects_invalid_version():
    with pytest.raises(editor_ops.GraphEditorUsageError):
        editor_ops.parse_graph_spec_input(
            {
                "version": 3,
                "nodes": [],
                "edges": [],
                "config": {},
            }
        )


def test_validate_graph_spec_returns_error_for_missing_edge_target():
    result = editor_ops.validate_graph_spec(
        {
            "version": 2,
            "nodes": [
                {
                    "id": "src",
                    "kind": "source",
                    "plugin": "schnitzel_stream.nodes.dev:StaticSource",
                    "config": {"packets": []},
                }
            ],
            "edges": [{"src": "src", "dst": "missing"}],
            "config": {},
        }
    )
    assert result.ok is False
    assert result.error


def test_render_profile_spec_with_invalid_camera_index_raises(tmp_path: Path):
    with pytest.raises(editor_ops.GraphEditorUsageError):
        editor_ops.render_profile_spec(
            repo_root=tmp_path,
            profile_id="inproc_demo",
            experimental=False,
            overrides={"camera_index": "invalid"},
        )
