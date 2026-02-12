from __future__ import annotations

# Zone 판정 단위 테스트

from ai.rules.zones import point_in_polygon, evaluate_zones


def test_point_in_polygon_basic():
    square = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert point_in_polygon((5, 5), square) is True
    assert point_in_polygon((15, 5), square) is False


def test_evaluate_zones_inside_outside():
    square = [[0, 0], [10, 0], [10, 10], [0, 10]]
    zones = [{"zone_id": "Z1", "polygon": square, "enabled": True}]
    rule_map = {"ZONE_INTRUSION": "bottom_center"}

    bbox_inside = {"x1": 2, "y1": 2, "x2": 4, "y2": 4}
    res1 = evaluate_zones("ZONE_INTRUSION", bbox_inside, zones, rule_map)
    assert res1["inside"] is True
    assert res1["zone_id"] == "Z1"

    bbox_out = {"x1": 20, "y1": 20, "x2": 30, "y2": 30}
    res2 = evaluate_zones("ZONE_INTRUSION", bbox_out, zones, rule_map)
    assert res2["inside"] is False
