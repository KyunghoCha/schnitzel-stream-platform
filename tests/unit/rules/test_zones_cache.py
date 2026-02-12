from __future__ import annotations

import json
from pathlib import Path

import ai.rules.zones as zones


def test_zones_api_cache_ttl(monkeypatch):
    calls = {"count": 0}

    def fake_fetch(*args, **kwargs):
        calls["count"] += 1
        return [{"zone_id": "Z1", "polygon": [[0, 0], [1, 0], [1, 1]]}]

    monkeypatch.setattr(zones, "fetch_zones_from_api", fake_fetch)

    cache = zones.ZoneCache(ttl_sec=30.0)
    base = 1000.0
    monkeypatch.setattr(zones, "_now_ts", lambda: base)

    result1 = zones.load_zones(
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
    monkeypatch.setattr(zones, "_now_ts", lambda: base + 5)
    result2 = zones.load_zones(
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
    monkeypatch.setattr(zones, "_now_ts", lambda: base + 31)
    result3 = zones.load_zones(
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

    def fake_fetch(*args, **kwargs):
        calls["count"] += 1
        return None

    monkeypatch.setattr(zones, "fetch_zones_from_api", fake_fetch)

    cache = zones.ZoneCache(ttl_sec=1.0)
    base = 3000.0
    monkeypatch.setattr(zones, "_now_ts", lambda: base)
    cache.set([{"zone_id": "Z9", "polygon": [[0, 0], [1, 0], [1, 1]]}])
    # expire cache so fetch is attempted, then fallback to stale cache
    monkeypatch.setattr(zones, "_now_ts", lambda: base + 2.0)

    result = zones.load_zones(
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

    cache = zones.ZoneCache(ttl_sec=30.0)
    base = 2000.0
    monkeypatch.setattr(zones, "_now_ts", lambda: base)

    result1 = zones.load_zones(
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
    monkeypatch.setattr(zones, "_now_ts", lambda: base + 5)
    result2 = zones.load_zones(
        source="file",
        site_id="S001",
        camera_id="cam01",
        api_cfg=None,
        file_path=str(zones_file),
        cache=cache,
    )
    assert result2 == result1

    # expire cache -> re-read file
    monkeypatch.setattr(zones, "_now_ts", lambda: base + 31)
    result3 = zones.load_zones(
        source="file",
        site_id="S001",
        camera_id="cam01",
        api_cfg=None,
        file_path=str(zones_file),
        cache=cache,
    )
    assert result3 != result1
    assert result3[0]["zone_id"] == "Z1"
