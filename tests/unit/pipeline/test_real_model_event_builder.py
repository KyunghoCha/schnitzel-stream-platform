from __future__ import annotations

from ai.pipeline.events import RealModelEventBuilder
from ai.pipeline.model_adapter import load_model_adapter


class _Adapter:
    def __init__(self, dets):
        self._dets = dets

    def infer(self, frame):
        return self._dets


def test_real_model_event_builder_maps_payloads():
    dets = [
        {
            "event_type": "ZONE_INTRUSION",
            "object_type": "PERSON",
            "severity": "LOW",
            "track_id": 7,
            "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
            "confidence": 0.9,
        },
        {
            "event_type": "FIRE_DETECTED",
            "object_type": "FIRE",
            "severity": "HIGH",
            "track_id": None,
            "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
            "confidence": 0.8,
        },
    ]
    builder = RealModelEventBuilder(
        site_id="S001",
        camera_id="C001",
        adapter=_Adapter(dets),
    )
    payloads = builder.build(12, None)
    assert len(payloads) == 2
    assert payloads[0]["site_id"] == "S001"
    assert payloads[0]["camera_id"] == "C001"
    assert payloads[0]["event_type"] == "ZONE_INTRUSION"
    assert payloads[0]["object_type"] == "PERSON"
    assert payloads[0]["track_id"] == 7
    assert payloads[0]["bbox"] == {"x1": 1, "y1": 2, "x2": 3, "y2": 4}
    assert payloads[0]["confidence"] == 0.9
    assert payloads[0]["event_id"]
    assert payloads[0]["ts"]


def test_real_model_event_builder_skips_invalid_detection():
    dets = [
        {"event_type": "ZONE_INTRUSION"},
        {
            "event_type": "ZONE_INTRUSION",
            "object_type": "PERSON",
            "severity": "LOW",
            "track_id": 1,
            "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
            "confidence": 0.9,
        },
    ]
    builder = RealModelEventBuilder(
        site_id="S001",
        camera_id="C001",
        adapter=_Adapter(dets),
    )
    payloads = builder.build(0, None)
    assert len(payloads) == 1
    assert payloads[0]["track_id"] == 1


def test_real_model_event_builder_requires_track_id_for_person():
    dets = [
        {
            "event_type": "ZONE_INTRUSION",
            "object_type": "PERSON",
            "severity": "LOW",
            "track_id": None,
            "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
            "confidence": 0.9,
        }
    ]
    builder = RealModelEventBuilder(
        site_id="S001",
        camera_id="C001",
        adapter=_Adapter(dets),
    )
    payloads = builder.build(0, None)
    assert payloads == []


def test_load_model_adapter_invalid_path():
    import pytest
    with pytest.raises(ValueError, match="module:ClassName"):
        load_model_adapter("no_colon_in_path")


def test_load_model_adapter_missing_class():
    import pytest
    with pytest.raises(ImportError, match="adapter class not found"):
        load_model_adapter("ai.pipeline.model_adapter:NoSuchClass")
