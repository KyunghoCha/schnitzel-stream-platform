from __future__ import annotations

from copy import deepcopy

import pytest

from ai.config import validate_config


def _base_cfg() -> dict:
    return {
        "app": {"site_id": "S001"},
        "ingest": {"fps_limit": 10},
        "events": {"post_url": "http://x"},
    }


def _deep_merge(dst: dict, src: dict) -> dict:
    out = deepcopy(dst)
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def _cfg_with(patch: dict) -> dict:
    return _deep_merge(_base_cfg(), patch)


def test_validate_config_missing_sections():
    with pytest.raises(ValueError):
        validate_config({})


def test_validate_config_snapshot_requires_base_dir():
    cfg = _cfg_with({"events": {"post_url": "http://x", "snapshot": {"public_prefix": "/snapshots"}}})
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_validate_config_rejects_duplicate_camera_id():
    cfg = _cfg_with(
        {
            "cameras": [
                {"id": "cam01", "source": {"type": "rtsp", "url": "rtsp://a"}},
                {"id": "cam01", "source": {"type": "rtsp", "url": "rtsp://b"}},
            ]
        }
    )
    with pytest.raises(ValueError, match="duplicate camera id"):
        validate_config(cfg)


def test_validate_config_rejects_non_int_webcam_index():
    cfg = _cfg_with(
        {
            "cameras": [
                {"id": "cam_webcam", "source": {"type": "webcam", "index": "0"}},
            ]
        }
    )
    with pytest.raises(ValueError, match="webcam source.index must be int"):
        validate_config(cfg)


def test_validate_config_rejects_non_str_events_emitter_adapter():
    cfg = _cfg_with({"events": {"post_url": "http://x", "emitter_adapter": 123}})
    with pytest.raises(ValueError, match="events.emitter_adapter must be str"):
        validate_config(cfg)


@pytest.mark.parametrize(
    ("patch", "match"),
    [
        ({"model": {"mode": "dummy"}}, r"model.mode must be 'real' or 'mock'"),
        ({"source": {"adapter": 123}}, r"source.adapter must be str"),
        ({"source": {"type": "bad"}}, r"unsupported source.type"),
        ({"sensor": {"enabled": "true"}}, r"sensor.enabled must be bool"),
        ({"sensor": {"enabled": True, "type": "ros2"}}, r"enabled sensor requires sensor.adapter"),
        ({"sensor": {"enabled": False, "adapters": 123}}, r"sensor.adapters must be list\[str\]"),
        ({"sensor": {"enabled": False, "adapters": ["", "pkg.s:Front"]}}, r"sensor.adapters items must be non-empty str"),
        ({"sensor": {"enabled": False, "queue_size": 0}}, r"sensor.queue_size must be positive int"),
        ({"sensor": {"enabled": False, "emit_events": "true"}}, r"sensor.emit_events must be bool"),
        ({"sensor": {"enabled": False, "emit_fused_events": "true"}}, r"sensor.emit_fused_events must be bool"),
        ({"zones": {"source": "bad"}}, r"zones.source must be one of: api, file, none"),
    ],
)
def test_validate_config_rejects_invalid_value_cases(patch: dict, match: str):
    cfg = _cfg_with(patch)
    with pytest.raises(ValueError, match=match):
        validate_config(cfg)


@pytest.mark.parametrize(
    ("source", "match"),
    [
        ({"type": "unknown"}, r"unsupported camera source.type"),
        ({"type": "plugin"}, r"plugin source requires source.adapter"),
    ],
)
def test_validate_config_rejects_invalid_camera_source(source: dict, match: str):
    cfg = _cfg_with({"cameras": [{"id": "cam_x", "source": source}]})
    with pytest.raises(ValueError, match=match):
        validate_config(cfg)


def test_validate_config_allows_zones_source_none():
    cfg = _cfg_with({"zones": {"source": "none"}})
    assert validate_config(cfg) is None


def test_validate_config_allows_enabled_sensor_with_adapters_only():
    cfg = _cfg_with(
        {
            "sensor": {
                "enabled": True,
                "adapters": ["pkg.sensors:FrontSensor", "pkg.sensors:RearSensor"],
            }
        }
    )
    assert validate_config(cfg) is None
