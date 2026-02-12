from __future__ import annotations

import json
import time

import ai.rules.zones as zones_mod
from ai.rules.zones import ZoneEvaluator


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

    def fake_fetch(*args, **kwargs):
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

    # 첫 apply는 캐시 없으므로 기본 zone 반환 + 비동기 fetch만 트리거
    t0 = time.monotonic()
    out = evaluator.apply(dict(payload))
    elapsed = time.monotonic() - t0
    assert elapsed < 0.15
    assert out["zone"]["inside"] is False

    # 백그라운드 fetch 완료까지 대기
    deadline = time.monotonic() + 2.0
    while calls["count"] < 1 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert calls["count"] == 1

    # 캐시가 채워지면 즉시 zone 판정 가능
    deadline = time.monotonic() + 2.0
    out2 = evaluator.apply(dict(payload))
    while out2["zone"]["inside"] is False and time.monotonic() < deadline:
        time.sleep(0.01)
        out2 = evaluator.apply(dict(payload))
    assert out2["zone"]["inside"] is True
    assert out2["zone"]["zone_id"] == "Z1"
