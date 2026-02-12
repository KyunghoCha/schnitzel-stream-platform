from __future__ import annotations

from ai.vision.class_mapping import load_class_map


def test_load_class_map(tmp_path) -> None:
    cfg = tmp_path / "map.yaml"
    cfg.write_text(
        """\
class_map:
  - class_id: 0
    event_type: ZONE_INTRUSION
    object_type: PERSON
    severity: LOW
  - class_id: 3
    event_type: PPE_VIOLATION
    object_type: PERSON
    severity: MEDIUM
""",
        encoding="utf-8",
    )
    out = load_class_map(str(cfg))
    assert 0 in out
    assert out[0].event_type == "ZONE_INTRUSION"
    assert 3 in out
    assert out[3].event_type == "PPE_VIOLATION"
