from __future__ import annotations

from argparse import Namespace
from types import SimpleNamespace

import pytest

from ai.pipeline import __main__ as mainmod
from ai.utils.metrics import MetricsTracker


def test_build_source_missing_video_override_raises(tmp_path):
    missing = tmp_path / "missing.mp4"
    with pytest.raises(FileNotFoundError, match="video file not found"):
        mainmod._build_source(
            source_type="file",
            video_override=str(missing),
            source_path=None,
            source_url=None,
            source_adapter=None,
            camera_index=0,
            rtsp_cfg=None,
        )


def test_main_rejects_video_with_rtsp_source_type(monkeypatch, tmp_path):
    monkeypatch.setattr(
        mainmod,
        "_parse_args",
        lambda: Namespace(
            camera_id=None,
            video=str(tmp_path / "a.mp4"),
            source_type="rtsp",
            dry_run=True,
            output_jsonl=None,
            max_events=1,
            visualize=False,
        ),
    )

    with pytest.raises(ValueError, match="cannot be combined"):
        mainmod.main()


def test_build_source_plugin_requires_adapter():
    with pytest.raises(RuntimeError, match="plugin source requires"):
        mainmod._build_source(
            source_type="plugin",
            video_override=None,
            source_path=None,
            source_url=None,
            source_adapter=None,
            camera_index=0,
            rtsp_cfg=None,
        )


def test_build_source_plugin_uses_loader(monkeypatch):
    class _Source:
        supports_reconnect = False
        is_live = False

        def read(self):
            return False, None

        def release(self):
            return None

        def fps(self):
            return 0.0

    monkeypatch.setattr(mainmod, "load_frame_source", lambda _path: _Source())
    source = mainmod._build_source(
        source_type="plugin",
        video_override=None,
        source_path=None,
        source_url=None,
        source_adapter="pkg.custom:MySource",
        camera_index=0,
        rtsp_cfg=None,
    )
    assert isinstance(source, _Source)


def test_parse_args_rejects_invalid_source_type(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--source-type", "invalid"])
    with pytest.raises(SystemExit):
        mainmod._parse_args()


def test_build_emitter_wires_metrics_delivery_callback(monkeypatch):
    monkeypatch.setattr(mainmod.socket, "gethostbyname", lambda _host: "127.0.0.1")
    settings = SimpleNamespace(
        events=SimpleNamespace(
            post_url="http://example.com/api/events",
            timeout_sec=1.0,
            retry_max_attempts=1,
            retry_backoff_sec=0.1,
        )
    )
    args = Namespace(output_jsonl=None, dry_run=False)
    metrics = MetricsTracker(interval_sec=9999, fps_window_sec=5)

    emitter = mainmod._build_emitter(settings, args, metrics)
    try:
        assert isinstance(emitter, mainmod.BackendEmitter)
        assert emitter.delivery_callback is not None
    finally:
        emitter.close()


def test_build_event_builder_rejects_unknown_mode():
    settings = SimpleNamespace(
        model=SimpleNamespace(mode="invalid", adapter=None),
        site_id="S001",
        camera_id="cam01",
        timezone="Asia/Seoul",
        events=SimpleNamespace(snapshot_public_prefix=None),
    )
    with pytest.raises(ValueError, match="unsupported model.mode"):
        mainmod._build_event_builder(settings, snapshot_base_dir=None)


def test_build_event_builder_real_requires_adapter():
    settings = SimpleNamespace(
        model=SimpleNamespace(mode="real", adapter=None),
        site_id="S001",
        camera_id="cam01",
        timezone="Asia/Seoul",
        events=SimpleNamespace(snapshot_public_prefix=None),
    )
    with pytest.raises(RuntimeError, match="requires AI_MODEL_ADAPTER"):
        mainmod._build_event_builder(settings, snapshot_base_dir=None)


def test_build_emitter_uses_custom_adapter_when_configured(monkeypatch):
    class _CustomEmitter:
        def emit(self, payload):
            return True

        def close(self):
            return None

    monkeypatch.setattr(mainmod, "load_event_emitter", lambda _path: _CustomEmitter())
    settings = SimpleNamespace(
        events=SimpleNamespace(
            emitter_adapter="pkg.custom:MyEmitter",
            post_url="http://example.com/api/events",
            timeout_sec=1.0,
            retry_max_attempts=1,
            retry_backoff_sec=0.1,
        )
    )
    args = Namespace(output_jsonl=None, dry_run=False)

    emitter = mainmod._build_emitter(settings, args, metrics=None)
    assert isinstance(emitter, _CustomEmitter)


def test_build_sensor_runtime_disabled_returns_none():
    settings = SimpleNamespace(
        sensor=SimpleNamespace(
            enabled=False,
            adapter=None,
            queue_size=256,
            type=None,
            topic=None,
        )
    )
    assert mainmod._build_sensor_runtime(settings) is None


def test_build_sensor_runtime_requires_adapter():
    settings = SimpleNamespace(
        sensor=SimpleNamespace(
            enabled=True,
            adapter=None,
            queue_size=256,
            type="ultrasonic",
            topic=None,
        )
    )
    with pytest.raises(RuntimeError, match="requires sensor.adapter"):
        mainmod._build_sensor_runtime(settings)


def test_build_sensor_runtime_uses_loader(monkeypatch):
    class _Sensor:
        supports_reconnect = False
        sensor_type = "ultrasonic"

        def read(self):
            return False, None

        def release(self):
            return None

    monkeypatch.setattr(mainmod, "load_sensor_source", lambda _path: _Sensor())
    settings = SimpleNamespace(
        sensor=SimpleNamespace(
            enabled=True,
            adapter="pkg.sensor:CustomSensor",
            queue_size=16,
            type="ultrasonic",
            topic="/sensors/front",
        )
    )
    runtime = mainmod._build_sensor_runtime(settings)
    assert runtime is not None
    runtime.stop()


def test_build_sensor_runtime_supports_multiple_adapters(monkeypatch):
    loaded: list[str] = []

    class _Sensor:
        supports_reconnect = False
        sensor_type = "ultrasonic"

        def read(self):
            return False, None

        def release(self):
            return None

    def _load(path: str):
        loaded.append(path)
        return _Sensor()

    monkeypatch.setattr(mainmod, "load_sensor_source", _load)
    settings = SimpleNamespace(
        sensor=SimpleNamespace(
            enabled=True,
            adapter=None,
            adapters=("pkg.sensor:FrontSensor", "pkg.sensor:RearSensor"),
            queue_size=16,
            type="ultrasonic",
            topic="/sensors/front",
        )
    )
    runtime = mainmod._build_sensor_runtime(settings)
    assert runtime is not None
    assert isinstance(runtime, mainmod.MultiSensorRuntime)
    assert loaded == ["pkg.sensor:FrontSensor", "pkg.sensor:RearSensor"]
    runtime.stop()


def test_resolve_sensor_adapter_paths_merges_single_and_multi():
    settings = SimpleNamespace(
        sensor=SimpleNamespace(
            adapter="pkg.sensor:Primary",
            adapters=("pkg.sensor:Primary", " pkg.sensor:Aux "),
        )
    )
    assert mainmod._resolve_sensor_adapter_paths(settings) == [
        "pkg.sensor:Primary",
        "pkg.sensor:Aux",
    ]
