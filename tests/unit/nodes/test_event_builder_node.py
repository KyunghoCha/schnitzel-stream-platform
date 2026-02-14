from __future__ import annotations

from uuid import NAMESPACE_DNS, uuid5

import pytest

from schnitzel_stream.nodes.event_builder import ProtocolV02EventBuilderNode
from schnitzel_stream.packet import StreamPacket


def test_event_builder_requires_site_id():
    with pytest.raises(ValueError):
        ProtocolV02EventBuilderNode(config={})


def test_event_builder_emits_deterministic_event_id_and_idempotency_key():
    node = ProtocolV02EventBuilderNode(config={"site_id": "S1", "camera_id": "cam01"})

    det = {
        "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
        "confidence": 0.75,
        "event_type": "ZONE_INTRUSION",
        "object_type": "PERSON",
        "severity": "LOW",
        "track_id": 123,
    }

    pkt1 = StreamPacket.new(kind="detection", source_id="cam01", ts="2026-02-14T00:00:00Z", payload=dict(det))
    pkt2 = StreamPacket.new(kind="detection", source_id="cam01", ts="2026-02-14T00:00:00Z", payload=dict(det))

    out1 = list(node.process(pkt1))
    out2 = list(node.process(pkt2))
    assert len(out1) == 1
    assert len(out2) == 1

    e1 = out1[0]
    e2 = out2[0]

    assert e1.kind == "event"
    assert e1.payload["site_id"] == "S1"
    assert e1.payload["camera_id"] == "cam01"
    assert e1.payload["bbox"] == det["bbox"]
    assert e1.payload["track_id"] == 123

    assert e1.meta["idempotency_key"] == e2.meta["idempotency_key"]
    assert e1.payload["event_id"] == e2.payload["event_id"]

    # source_packet_id is expected to differ.
    assert e1.meta["source_packet_id"] != e2.meta["source_packet_id"]

    namespace = uuid5(NAMESPACE_DNS, "schnitzel_stream:event_protocol_v0.2")
    assert e1.payload["event_id"] == str(uuid5(namespace, e1.meta["idempotency_key"]))


def test_event_builder_skips_invalid_detections_and_handles_lists():
    node = ProtocolV02EventBuilderNode(config={"site_id": "S1"})

    det_valid = {
        "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
        "confidence": 0.9,
        "event_type": "FIRE_DETECTED",
        "object_type": "FIRE",
        "severity": "HIGH",
    }
    det_invalid = {"confidence": 0.1}  # missing required fields

    pkt = StreamPacket.new(
        kind="detection",
        source_id="cam99",
        ts="2026-02-14T00:00:00Z",
        payload=[det_invalid, det_valid],
    )
    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].payload["camera_id"] == "cam99"
    assert out[0].payload["event_type"] == "FIRE_DETECTED"
    assert node.skipped_total >= 1

