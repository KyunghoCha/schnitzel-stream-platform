from __future__ import annotations

# Dedup 로직 단위 테스트

from ai.rules.dedup import DedupController


def test_dedup_cooldown_and_severity_override():
    ctrl = DedupController(cooldown_sec=1.0, prune_interval=1)
    payload = {"camera_id": "C1", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "LOW"}
    assert ctrl.allow_emit(payload) is True
    assert ctrl.allow_emit(payload) is False  # 쿨다운

    payload2 = {"camera_id": "C1", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "HIGH"}
    assert ctrl.allow_emit(payload2) is True  # severity 변경 시 허용
