from __future__ import annotations

import pytest

from ai.pipeline import config as cfg


def _fake_load_configs():
    return {
        "app": {"site_id": "S001"},
        "ingest": {"fps_limit": 10},
        "events": {"post_url": "http://x"},
        "cameras": [
            {"id": "cam_file", "enabled": True, "source": {"type": "file", "path": "data/a.mp4"}},
            {"id": "cam_rtsp", "enabled": True, "source": {"type": "rtsp", "url": "rtsp://x"}},
        ],
    }


def test_source_type_override_prefers_matching_camera(monkeypatch):
    monkeypatch.setattr(cfg, "_load_configs", _fake_load_configs)

    settings = cfg.load_pipeline_settings(camera_id=None, source_type_override="rtsp")
    assert settings.source.type == "rtsp"
    assert settings.source.url == "rtsp://x"


def test_invalid_camera_id_raises(monkeypatch):
    monkeypatch.setattr(cfg, "_load_configs", _fake_load_configs)

    with pytest.raises(ValueError, match="camera_id not found"):
        cfg.load_pipeline_settings(camera_id="missing-camera")


def test_video_override_forces_file_source(monkeypatch, tmp_path):
    monkeypatch.setattr(cfg, "_load_configs", _fake_load_configs)
    video_path = tmp_path / "override.mp4"

    settings = cfg.load_pipeline_settings(
        camera_id="cam_rtsp",
        video_override=str(video_path),
    )

    assert settings.source.type == "file"
    assert settings.source.path == str(video_path)
    assert settings.source.url is None


def test_relative_source_path_is_resolved_from_project_root(monkeypatch, tmp_path):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_file",
                    "enabled": True,
                    "source": {"type": "file", "path": "tests/play/sample.mp4"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    monkeypatch.setattr(cfg, "resolve_project_root", lambda: tmp_path)

    settings = cfg.load_pipeline_settings(camera_id="cam_file")
    assert settings.source.path == str((tmp_path / "tests" / "play" / "sample.mp4").resolve())


def test_webcam_index_is_loaded_from_camera_config(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_webcam",
                    "enabled": True,
                    "source": {"type": "webcam", "index": 2},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)

    settings = cfg.load_pipeline_settings(camera_id="cam_webcam")
    assert settings.source.type == "webcam"
    assert settings.source.index == 2


def test_events_emitter_adapter_loaded(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "ingest": {"fps_limit": 10},
            "events": {
                "post_url": "http://x",
                "emitter_adapter": "pkg.custom:MyEmitter",
            },
            "cameras": [
                {"id": "cam_file", "enabled": True, "source": {"type": "file", "path": "data/a.mp4"}}
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)

    settings = cfg.load_pipeline_settings(camera_id="cam_file")
    assert settings.events.emitter_adapter == "pkg.custom:MyEmitter"


def test_plugin_source_adapter_loaded_from_camera_source(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_plugin",
                    "enabled": True,
                    "source": {"type": "plugin", "adapter": "pkg.sources:MySource"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    settings = cfg.load_pipeline_settings(camera_id="cam_plugin")
    assert settings.source.type == "plugin"
    assert settings.source.adapter == "pkg.sources:MySource"


def test_global_source_adapter_override_wins(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "source": {"adapter": "pkg.sources:GlobalSource"},
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_plugin",
                    "enabled": True,
                    "source": {"type": "plugin", "adapter": "pkg.sources:CameraSource"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    settings = cfg.load_pipeline_settings(camera_id="cam_plugin")
    assert settings.source.adapter == "pkg.sources:GlobalSource"


def test_global_source_type_override_applies(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "source": {"type": "plugin", "adapter": "pkg.sources:GlobalSource"},
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_file",
                    "enabled": True,
                    "source": {"type": "file", "path": "data/a.mp4"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    settings = cfg.load_pipeline_settings(camera_id="cam_file")
    assert settings.source.type == "plugin"
    assert settings.source.adapter == "pkg.sources:GlobalSource"


def test_sensor_settings_loaded(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "sensor": {
                "enabled": True,
                "type": "ros2",
                "adapter": "pkg.sensors:Ros2Sensor",
                "adapters": ["pkg.sensors:AuxSensor"],
                "topic": "/sensors/front",
                "queue_size": 512,
                "time_window_ms": 450,
                "emit_events": True,
                "emit_fused_events": True,
            },
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_file",
                    "enabled": True,
                    "source": {"type": "file", "path": "data/a.mp4"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    settings = cfg.load_pipeline_settings(camera_id="cam_file")
    assert settings.sensor.enabled is True
    assert settings.sensor.type == "ros2"
    assert settings.sensor.adapter == "pkg.sensors:Ros2Sensor"
    assert settings.sensor.adapters == ("pkg.sensors:Ros2Sensor", "pkg.sensors:AuxSensor")
    assert settings.sensor.topic == "/sensors/front"
    assert settings.sensor.queue_size == 512
    assert settings.sensor.time_window_ms == 450
    assert settings.sensor.emit_events is True
    assert settings.sensor.emit_fused_events is True


def test_sensor_settings_support_comma_separated_adapters(monkeypatch):
    def _fake_cfg():
        return {
            "app": {"site_id": "S001"},
            "sensor": {
                "enabled": True,
                "adapters": "pkg.sensors:FrontSensor, pkg.sensors:RearSensor",
            },
            "ingest": {"fps_limit": 10},
            "events": {"post_url": "http://x"},
            "cameras": [
                {
                    "id": "cam_file",
                    "enabled": True,
                    "source": {"type": "file", "path": "data/a.mp4"},
                }
            ],
        }

    monkeypatch.setattr(cfg, "_load_configs", _fake_cfg)
    settings = cfg.load_pipeline_settings(camera_id="cam_file")
    assert settings.sensor.enabled is True
    assert settings.sensor.adapter == "pkg.sensors:FrontSensor"
    assert settings.sensor.adapters == ("pkg.sensors:FrontSensor", "pkg.sensors:RearSensor")
