from __future__ import annotations

from schnitzel_stream.contracts.payload_profile import is_profile_compatible, normalize_profile
from schnitzel_stream.graph.compat import GraphCompatibilityError, validate_graph_compat
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec


def test_payload_profile_normalize_and_matrix():
    assert normalize_profile(None) is None
    assert normalize_profile(" json_portable ") == "json_portable"

    assert is_profile_compatible("inproc_any", "inproc_any")
    assert not is_profile_compatible("inproc_any", "json_portable")
    assert is_profile_compatible("json_portable", "json_portable")
    assert is_profile_compatible("ref_portable", "json_portable")
    assert is_profile_compatible("ref_portable", "ref_portable")


def test_graph_compat_rejects_profile_mismatch_inproc_to_json_portable():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.packs.vision.nodes.video:OpenCvVideoFileSource",
            config={},
        ),
        NodeSpec(
            node_id="sink",
            kind="sink",
            plugin="schnitzel_stream.nodes.file_sink:JsonlSink",
            config={"path": "out.jsonl"},
        ),
    ]
    edges = [EdgeSpec(src="src", dst="sink")]

    try:
        validate_graph_compat(nodes, edges, transport="inproc")
    except GraphCompatibilityError as exc:
        assert "payload profile mismatch" in str(exc)
    else:
        raise AssertionError("expected GraphCompatibilityError")


def test_graph_compat_accepts_ref_portable_to_json_portable():
    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={"packets": []},
        ),
        NodeSpec(
            node_id="to_ref",
            kind="node",
            plugin="schnitzel_stream.nodes.blob_ref:BytesToFileRefNode",
            config={"dir": "./outputs/blobs"},
        ),
        NodeSpec(
            node_id="sink",
            kind="sink",
            plugin="schnitzel_stream.nodes.file_sink:JsonlSink",
            config={"path": "out.jsonl"},
        ),
    ]
    edges = [
        EdgeSpec(src="src", dst="to_ref"),
        EdgeSpec(src="to_ref", dst="sink"),
    ]

    assert validate_graph_compat(nodes, edges, transport="inproc") is None
