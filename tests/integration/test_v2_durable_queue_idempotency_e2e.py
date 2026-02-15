from __future__ import annotations

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner
from schnitzel_stream.state.sqlite_queue import SqliteQueue


def test_v2_durable_queue_produces_stable_idempotency_keys(tmp_path):
    db_path = tmp_path / "events.sqlite3"

    nodes = [
        NodeSpec(
            node_id="frames",
            kind="source",
            plugin="schnitzel_stream.nodes.dev:StaticSource",
            config={
                "packets": [
                    {"kind": "frame", "source_id": "cam01", "ts": "2026-02-14T00:00:00Z", "payload": {"frame": None, "frame_idx": 0}},
                    {"kind": "frame", "source_id": "cam01", "ts": "2026-02-14T00:00:01Z", "payload": {"frame": None, "frame_idx": 1}},
                    {"kind": "frame", "source_id": "cam01", "ts": "2026-02-14T00:00:02Z", "payload": {"frame": None, "frame_idx": 2}},
                ]
            },
        ),
        NodeSpec(
            node_id="sample",
            kind="node",
            plugin="schnitzel_stream.nodes.video:EveryNthFrameSamplerNode",
            config={"every_n": 1},
        ),
        NodeSpec(
            node_id="detect",
            kind="node",
            plugin="schnitzel_stream.nodes.mock_detection:MockDetectorNode",
            config={
                "emit_every_n": 1,
                "event_type": "ZONE_INTRUSION",
                "object_type": "PERSON",
                "severity": "LOW",
                "confidence": 0.75,
                "track_id": "frame_idx",
                "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4},
            },
        ),
        NodeSpec(
            node_id="events",
            kind="node",
            plugin="schnitzel_stream.nodes.event_builder:ProtocolV02EventBuilderNode",
            config={"site_id": "S001"},
        ),
        NodeSpec(
            node_id="zones",
            kind="node",
            plugin="schnitzel_stream.nodes.policy:ZonePolicyNode",
            config={
                "rule_map": {"ZONE_INTRUSION": "bottom_center"},
                "zones": [{"zone_id": "Z1", "enabled": True, "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}],
            },
        ),
        NodeSpec(
            node_id="dedup",
            kind="node",
            plugin="schnitzel_stream.nodes.policy:DedupPolicyNode",
            config={"cooldown_sec": 9999.0, "prune_interval": 1},
        ),
        NodeSpec(
            node_id="q",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink",
            config={"path": str(db_path), "forward": False},
        ),
    ]
    edges = [
        EdgeSpec(src="frames", dst="sample"),
        EdgeSpec(src="sample", dst="detect"),
        EdgeSpec(src="detect", dst="events"),
        EdgeSpec(src="events", dst="zones"),
        EdgeSpec(src="zones", dst="dedup"),
        EdgeSpec(src="dedup", dst="q"),
    ]

    # Two runs should not create duplicates because event builder emits stable meta.idempotency_key.
    InProcGraphRunner().run(nodes=nodes, edges=edges)
    InProcGraphRunner().run(nodes=nodes, edges=edges)

    q = SqliteQueue(db_path)
    try:
        rows = q.read(limit=100)
        assert len(rows) == 3
    finally:
        q.close()

    # Drain + ack: queue should become empty.
    drain_nodes = [
        NodeSpec(
            node_id="src",
            kind="source",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource",
            config={"path": str(db_path), "limit": 100, "delete_on_emit": False},
        ),
        NodeSpec(node_id="op", kind="node", plugin="schnitzel_stream.nodes.dev:Identity"),
        NodeSpec(
            node_id="ack",
            kind="sink",
            plugin="schnitzel_stream.nodes.durable_sqlite:SqliteQueueAckSink",
            config={"path": str(db_path)},
        ),
    ]
    drain_edges = [EdgeSpec(src="src", dst="op"), EdgeSpec(src="op", dst="ack")]

    result = InProcGraphRunner().run(nodes=drain_nodes, edges=drain_edges)
    assert len(result.outputs_by_node["src"]) == 3

    q2 = SqliteQueue(db_path)
    try:
        assert q2.read(limit=10) == []
    finally:
        q2.close()
