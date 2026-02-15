from __future__ import annotations

import json
import time

import schnitzel_stream.packs.vision.policy.zones as zones_mod
from schnitzel_stream.packs.vision.policy.zones import ZoneEvaluator, evaluate_zones, point_in_polygon


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


def test_zone_evaluator_file_source(tmp_path):
    zones = [
        {
            "zone_id": "Z1",
            "enabled": True,
            "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
        }
    ]
    zone_file = tmp_path / "zones.json"
    zone_file.write_text(json.dumps(zones), encoding="utf-8")

    evaluator = ZoneEvaluator(
        source="file",
        site_id="S1",
        camera_id="C1",
        rule_map={"ZONE_INTRUSION": "bottom_center"},
        file_path=str(zone_file),
    )

    payload = {"event_type": "ZONE_INTRUSION", "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4}}
    out = evaluator.apply(payload)
    assert out["zone"]["inside"] is True
    assert out["zone"]["zone_id"] == "Z1"


def test_zone_evaluator_api_refreshes_async_without_blocking(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(*_args, **_kwargs):
        calls["count"] += 1
        time.sleep(0.2)
        return [
            {
                "zone_id": "Z1",
                "enabled": True,
                "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
            }
        ]

    monkeypatch.setattr(zones_mod, "fetch_zones_from_api", fake_fetch)

    evaluator = ZoneEvaluator(
        source="api",
        site_id="S1",
        camera_id="C1",
        rule_map={"ZONE_INTRUSION": "bottom_center"},
        api_cfg={
            "base_url": "http://backend:8080",
            "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
            "timeout_sec": 1.0,
        },
        cache_ttl_sec=30.0,
    )

    payload = {"event_type": "ZONE_INTRUSION", "bbox": {"x1": 2, "y1": 2, "x2": 4, "y2": 4}}

    # First apply: no cache yet -> default zone + async fetch trigger only.
    t0 = time.monotonic()
    out = evaluator.apply(dict(payload))
    elapsed = time.monotonic() - t0
    assert elapsed < 0.15
    assert out["zone"]["inside"] is False

    # Wait for background fetch.
    deadline = time.monotonic() + 2.0
    while calls["count"] < 1 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert calls["count"] == 1

    # Once cached, evaluation should be immediate.
    deadline = time.monotonic() + 2.0
    out2 = evaluator.apply(dict(payload))
    while out2["zone"]["inside"] is False and time.monotonic() < deadline:
        time.sleep(0.01)
        out2 = evaluator.apply(dict(payload))
    assert out2["zone"]["inside"] is True
    assert out2["zone"]["zone_id"] == "Z1"


def test_zones_api_cache_ttl(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(*_args, **_kwargs):
        calls["count"] += 1
        return [{"zone_id": "Z1", "polygon": [[0, 0], [1, 0], [1, 1]]}]

    monkeypatch.setattr(zones_mod, "fetch_zones_from_api", fake_fetch)

    cache = zones_mod.ZoneCache(ttl_sec=30.0)
    base = 1000.0
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base)

    result1 = zones_mod.load_zones(
        source="api",
        site_id="S001",
        camera_id="cam01",
        api_cfg={
            "base_url": "http://backend:8080",
            "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
            "timeout_sec": 1.0,
        },
        file_path=None,
        cache=cache,
    )
    assert calls["count"] == 1
    assert result1

    # within TTL -> cache hit
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base + 5)
    result2 = zones_mod.load_zones(
        source="api",
        site_id="S001",
        camera_id="cam01",
        api_cfg={
            "base_url": "http://backend:8080",
            "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
            "timeout_sec": 1.0,
        },
        file_path=None,
        cache=cache,
    )
    assert calls["count"] == 1
    assert result2 == result1

    # expire cache -> refetch
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base + 31)
    result3 = zones_mod.load_zones(
        source="api",
        site_id="S001",
        camera_id="cam01",
        api_cfg={
            "base_url": "http://backend:8080",
            "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
            "timeout_sec": 1.0,
        },
        file_path=None,
        cache=cache,
    )
    assert calls["count"] == 2
    assert result3 == result1


def test_zones_api_fallback_to_cached_on_error(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(*_args, **_kwargs):
        calls["count"] += 1
        return None

    monkeypatch.setattr(zones_mod, "fetch_zones_from_api", fake_fetch)

    cache = zones_mod.ZoneCache(ttl_sec=1.0)
    base = 3000.0
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base)
    cache.set([{"zone_id": "Z9", "polygon": [[0, 0], [1, 0], [1, 1]]}])
    # expire cache so fetch is attempted, then fallback to stale cache
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base + 2.0)

    result = zones_mod.load_zones(
        source="api",
        site_id="S001",
        camera_id="cam01",
        api_cfg={
            "base_url": "http://backend:8080",
            "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
            "timeout_sec": 1.0,
        },
        file_path=None,
        cache=cache,
    )
    assert calls["count"] == 1
    assert result == [{"zone_id": "Z9", "polygon": [[0, 0], [1, 0], [1, 1]]}]


def test_zones_file_cache_ttl(tmp_path, monkeypatch):
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps([{"zone_id": "Z0", "polygon": [[0, 0], [1, 0], [1, 1]]}]))

    cache = zones_mod.ZoneCache(ttl_sec=30.0)
    base = 2000.0
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base)

    result1 = zones_mod.load_zones(
        source="file",
        site_id="S001",
        camera_id="cam01",
        api_cfg=None,
        file_path=str(zones_file),
        cache=cache,
    )
    assert result1

    # overwrite file but cache should still return old
    zones_file.write_text(json.dumps([{"zone_id": "Z1", "polygon": [[0, 0], [1, 0], [1, 1]]}]))
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base + 5)
    result2 = zones_mod.load_zones(
        source="file",
        site_id="S001",
        camera_id="cam01",
        api_cfg=None,
        file_path=str(zones_file),
        cache=cache,
    )
    assert result2 == result1

    # expire cache -> re-read file
    monkeypatch.setattr(zones_mod, "_now_ts", lambda: base + 31)
    result3 = zones_mod.load_zones(
        source="file",
        site_id="S001",
        camera_id="cam01",
        api_cfg=None,
        file_path=str(zones_file),
        cache=cache,
    )
    assert result3 != result1
    assert result3[0]["zone_id"] == "Z1"
