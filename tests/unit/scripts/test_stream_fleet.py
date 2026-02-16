from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_stream_fleet_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "stream_fleet.py"
    spec = importlib.util.spec_from_file_location("stream_fleet_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_stream_specs_filters_disabled(tmp_path: Path):
    mod = _load_stream_fleet_module()
    cfg = tmp_path / "fleet.yaml"
    cfg.write_text(
        """
        streams:
          - id: stream01
            enabled: true
            input:
              type: rtsp
              url: rtsp://127.0.0.1:8554/stream1
          - id: stream02
            enabled: false
            input:
              type: webcam
              index: 0
        """,
        encoding="utf-8",
    )

    specs = mod.load_stream_specs(cfg)
    assert [s.stream_id for s in specs] == ["stream01"]
    assert specs[0].input_type == "rtsp"


def test_load_stream_specs_supports_legacy_camera_source_schema(tmp_path: Path):
    mod = _load_stream_fleet_module()
    cfg = tmp_path / "legacy_cameras.yaml"
    cfg.write_text(
        """
        cameras:
          - id: cam01
            enabled: true
            source:
              type: file
              path: data/samples/2048246-hd_1920_1080_24fps.mp4
        """,
        encoding="utf-8",
    )

    specs = mod.load_stream_specs(cfg)
    assert len(specs) == 1
    assert specs[0].stream_id == "cam01"
    assert specs[0].input_type == "file"


def test_stream_env_maps_input_types_and_legacy_keys():
    mod = _load_stream_fleet_module()

    rtsp_env = mod._stream_env(
        mod.StreamSpec(
            stream_id="stream01",
            input_type="rtsp",
            input_cfg={"type": "rtsp", "url": "rtsp://127.0.0.1:8554/stream1"},
        )
    )
    assert rtsp_env["SS_STREAM_ID"] == "stream01"
    assert rtsp_env["SS_INPUT_PLUGIN"].endswith(":OpenCvRtspSource")
    assert rtsp_env["SS_INPUT_URL"].startswith("rtsp://")
    assert rtsp_env["SS_CAMERA_ID"] == "stream01"
    assert rtsp_env["SS_SOURCE_URL"].startswith("rtsp://")

    file_env = mod._stream_env(
        mod.StreamSpec(
            stream_id="stream02",
            input_type="file",
            input_cfg={"type": "file", "path": "data/samples/2048246-hd_1920_1080_24fps.mp4"},
        )
    )
    assert file_env["SS_INPUT_PLUGIN"].endswith(":OpenCvVideoFileSource")
    assert Path(file_env["SS_INPUT_PATH"]).is_absolute()
    assert Path(file_env["SS_SOURCE_PATH"]).is_absolute()

    webcam_env = mod._stream_env(
        mod.StreamSpec(
            stream_id="stream03",
            input_type="webcam",
            input_cfg={"type": "webcam", "index": 2},
        )
    )
    assert webcam_env["SS_INPUT_PLUGIN"].endswith(":OpenCvWebcamSource")
    assert webcam_env["SS_INPUT_INDEX"] == "2"
    assert webcam_env["SS_CAMERA_INDEX"] == "2"

    plugin_env = mod._stream_env(
        mod.StreamSpec(
            stream_id="stream04",
            input_type="plugin",
            input_cfg={"type": "plugin", "plugin": "my_org.nodes:CustomSource"},
        )
    )
    assert plugin_env["SS_INPUT_PLUGIN"] == "my_org.nodes:CustomSource"
    assert plugin_env["SS_SOURCE_PLUGIN"] == "my_org.nodes:CustomSource"


def test_cmd_start_uses_graph_template_and_env(monkeypatch, tmp_path: Path):
    mod = _load_stream_fleet_module()

    cfg = tmp_path / "fleet.yaml"
    cfg.write_text(
        """
        streams:
          - id: stream01
            enabled: true
            input:
              type: rtsp
              url: rtsp://127.0.0.1:8554/stream1
        """,
        encoding="utf-8",
    )

    graph = tmp_path / "graph.yaml"
    graph.write_text("version: 2\nnodes: []\nedges: []\nconfig: {}\n", encoding="utf-8")

    calls: list[tuple[list[str], dict[str, str]]] = []

    def _fake_start(cmd, log_path, pid_path, env):
        calls.append((cmd, dict(env)))
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text("12345", encoding="utf-8")
        return 12345

    monkeypatch.setattr(mod, "start_process", _fake_start)

    args = argparse.Namespace(
        config=str(cfg),
        graph_template=str(graph),
        log_dir=str(tmp_path / "logs"),
        streams="",
        extra_args="--max-events 5",
    )

    mod.cmd_start(args)

    assert len(calls) == 1
    cmd, env = calls[0]
    assert "--graph" in cmd
    assert str(graph) in cmd
    assert "--max-events" in cmd
    assert env["SS_STREAM_ID"] == "stream01"
    assert env["SS_INPUT_TYPE"] == "rtsp"
    assert env["SS_INPUT_URL"] == "rtsp://127.0.0.1:8554/stream1"
