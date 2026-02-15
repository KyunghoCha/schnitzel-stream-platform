from __future__ import annotations

from schnitzel_stream.graph.compat import GraphCompatibilityError, validate_graph_compat
from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.packs.vision.nodes import DedupPolicyNode, ZonePolicyNode
from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def test_zone_policy_node_inline_zones():
    node = ZonePolicyNode(
        node_id="zones",
        config={
            "rule_map": {"ZONE_INTRUSION": "bottom_center"},
            "zones": [{"zone_id": "Z1", "enabled": True, "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}],
        },
    )
    pkt = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"event_type": "ZONE_INTRUSION", "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4}},
    )

    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].payload["zone"]["inside"] is True
    assert out[0].payload["zone"]["zone_id"] == "Z1"


def test_dedup_policy_node_filters_duplicates_and_allows_severity_change():
    node = DedupPolicyNode(node_id="dedup", config={"cooldown_sec": 1.0, "prune_interval": 1})

    pkt1 = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"camera_id": "cam01", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "LOW"},
    )
    pkt2 = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"camera_id": "cam01", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "LOW"},
    )
    pkt3 = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"camera_id": "cam01", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "HIGH"},
    )

    assert list(node.process(pkt1)) == [pkt1]
    assert list(node.process(pkt2)) == []
    assert list(node.process(pkt3)) == [pkt3]


def test_graph_compat_rejects_kind_mismatch_for_policy_nodes():
    nodes = [
        NodeSpec(node_id="src", kind="source", plugin="schnitzel_stream.nodes.dev:FooSource"),
        NodeSpec(node_id="zones", kind="node", plugin="schnitzel_stream.packs.vision.nodes:ZonePolicyNode"),
    ]
    edges = [EdgeSpec(src="src", dst="zones")]
    try:
        validate_graph_compat(nodes, edges, transport="inproc")
    except GraphCompatibilityError:
        return
    raise AssertionError("expected GraphCompatibilityError for kind mismatch (foo -> event)")


def test_inproc_graph_with_zone_and_dedup_nodes_filters_as_expected():
    runner = InProcGraphRunner()

    nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {
                        "kind": "event",
                        "source_id": "cam01",
                        "payload": {
                            "event_type": "ZONE_INTRUSION",
                            "camera_id": "cam01",
                            "track_id": 1,
                            "severity": "LOW",
                            "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4},
                        },
                    },
                    {
                        "kind": "event",
                        "source_id": "cam01",
                        "payload": {
                            "event_type": "ZONE_INTRUSION",
                            "camera_id": "cam01",
                            "track_id": 1,
                            "severity": "LOW",
                            "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4},
                        },
                    },
                    {
                        "kind": "event",
                        "source_id": "cam01",
                        "payload": {
                            "event_type": "ZONE_INTRUSION",
                            "camera_id": "cam01",
                            "track_id": 1,
                            "severity": "HIGH",
                            "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4},
                        },
                    },
                ]
            },
        ),
        NodeSpec(
            node_id="zones",
            kind="node",
            plugin="schnitzel_stream.packs.vision.nodes:ZonePolicyNode",
            config={
                "rule_map": {"ZONE_INTRUSION": "bottom_center"},
                "zones": [{"zone_id": "Z1", "enabled": True, "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}],
            },
        ),
        NodeSpec(
            node_id="dedup",
            kind="node",
            plugin="schnitzel_stream.packs.vision.nodes:DedupPolicyNode",
            config={"cooldown_sec": 10.0, "prune_interval": 1},
        ),
        NodeSpec(
            node_id="out",
            kind="sink",
            plugin="schnitzel_stream.nodes.dev:PrintSink",
            config={"prefix": "TEST ", "forward": True},
        ),
    ]
    edges = [
        EdgeSpec(src="src", dst="zones"),
        EdgeSpec(src="zones", dst="dedup"),
        EdgeSpec(src="dedup", dst="out"),
    ]

    result = runner.run(nodes=nodes, edges=edges)

    # 3 inputs -> zone node sees all, dedup drops 1, sink forwards only accepted.
    assert result.metrics["node.zones.consumed"] == 3
    assert result.metrics["node.dedup.consumed"] == 3
    assert result.metrics["node.out.produced"] == 2
    assert result.metrics["node.dedup.accepted_total"] == 2
    assert result.metrics["node.dedup.dropped_total"] == 1

    outs = result.outputs_by_node["out"]
    assert len(outs) == 2
    assert outs[0].payload["zone"]["inside"] is True
