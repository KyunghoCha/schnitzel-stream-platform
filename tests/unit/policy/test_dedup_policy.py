from __future__ import annotations

from schnitzel_stream.policy.dedup import DedupController


def test_dedup_cooldown_and_severity_override():
    ctrl = DedupController(cooldown_sec=1.0, prune_interval=1)
    payload = {"camera_id": "C1", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "LOW"}
    assert ctrl.allow_emit(payload) is True
    assert ctrl.allow_emit(payload) is False  # cooldown

    payload2 = {"camera_id": "C1", "event_type": "ZONE_INTRUSION", "track_id": 1, "severity": "HIGH"}
    assert ctrl.allow_emit(payload2) is True  # allow on severity change

