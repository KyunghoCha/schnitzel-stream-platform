from __future__ import annotations

from schnitzel_stream.nodes.mock_detection import MockDetectorNode
from schnitzel_stream.packet import StreamPacket


def test_mock_detector_emits_detection_with_required_fields():
    node = MockDetectorNode(config={"emit_every_n": 1})
    pkt = StreamPacket.new(kind="frame", source_id="cam01", ts="2026-02-14T00:00:00Z", payload={"frame": None, "frame_idx": 7})

    out = list(node.process(pkt))
    assert len(out) == 1
    det_pkt = out[0]
    assert det_pkt.kind == "detection"
    assert det_pkt.source_id == "cam01"
    assert det_pkt.ts == "2026-02-14T00:00:00Z"
    assert isinstance(det_pkt.payload, dict)
    assert det_pkt.payload["event_type"] == "ZONE_INTRUSION"
    assert det_pkt.payload["object_type"] == "PERSON"
    assert det_pkt.payload["severity"] == "LOW"
    assert "bbox" in det_pkt.payload
    assert det_pkt.payload["track_id"] == 7


def test_mock_detector_respects_emit_every_n_and_bbox_dx():
    node = MockDetectorNode(
        config={
            "emit_every_n": 2,
            "bbox": {"x1": 10, "y1": 0, "x2": 20, "y2": 10},
            "bbox_dx": 3,
        }
    )

    pkt1 = StreamPacket.new(kind="frame", source_id="cam01", payload={"frame": None, "frame_idx": 1})
    assert list(node.process(pkt1)) == []

    pkt2 = StreamPacket.new(kind="frame", source_id="cam01", payload={"frame": None, "frame_idx": 2})
    out2 = list(node.process(pkt2))
    assert len(out2) == 1
    bbox = out2[0].payload["bbox"]
    assert bbox["x1"] == 10 + 3 * 2
    assert bbox["x2"] == 20 + 3 * 2

