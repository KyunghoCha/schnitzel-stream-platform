from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_multi_cam_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "multi_cam.py"
    spec = importlib.util.spec_from_file_location("multi_cam_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_camera_specs_filters_disabled(tmp_path: Path):
    mod = _load_multi_cam_module()
    cfg = tmp_path / "cameras.yaml"
    cfg.write_text(
        """
        cameras:
          - id: cam01
            enabled: true
            source:
              type: rtsp
              url: rtsp://127.0.0.1:8554/stream1
          - id: cam02
            enabled: false
            source:
              type: webcam
              index: 0
        """,
        encoding="utf-8",
    )

    specs = mod.load_camera_specs(cfg)
    assert [s.camera_id for s in specs] == ["cam01"]
    assert specs[0].source_type == "rtsp"


def test_camera_env_maps_source_types():
    mod = _load_multi_cam_module()

    rtsp_env = mod._camera_env(
        mod.CameraSpec(
            camera_id="cam01",
            source_type="rtsp",
            source={"type": "rtsp", "url": "rtsp://127.0.0.1:8554/stream1"},
        )
    )
    assert rtsp_env["SS_SOURCE_PLUGIN"].endswith(":OpenCvRtspSource")
    assert rtsp_env["SS_SOURCE_URL"].startswith("rtsp://")

    file_env = mod._camera_env(
        mod.CameraSpec(
            camera_id="cam02",
            source_type="file",
            source={"type": "file", "path": "tests/play/2048246-hd_1920_1080_24fps.mp4"},
        )
    )
    assert file_env["SS_SOURCE_PLUGIN"].endswith(":OpenCvVideoFileSource")
    assert Path(file_env["SS_SOURCE_PATH"]).is_absolute()

    webcam_env = mod._camera_env(
        mod.CameraSpec(
            camera_id="cam03",
            source_type="webcam",
            source={"type": "webcam", "index": 2},
        )
    )
    assert webcam_env["SS_SOURCE_PLUGIN"].endswith(":OpenCvWebcamSource")
    assert webcam_env["SS_CAMERA_INDEX"] == "2"

    plugin_env = mod._camera_env(
        mod.CameraSpec(
            camera_id="cam04",
            source_type="plugin",
            source={"type": "plugin", "plugin": "my_org.nodes:CustomSource"},
        )
    )
    assert plugin_env["SS_SOURCE_PLUGIN"] == "my_org.nodes:CustomSource"


def test_cmd_start_uses_graph_template_and_env(monkeypatch, tmp_path: Path):
    mod = _load_multi_cam_module()

    cfg = tmp_path / "cameras.yaml"
    cfg.write_text(
        """
        cameras:
          - id: cam01
            enabled: true
            source:
              type: rtsp
              url: rtsp://127.0.0.1:8554/stream1
        """,
        encoding="utf-8",
    )

    graph = tmp_path / "graph.yaml"
    graph.write_text("version: 2\nnodes: []\nedges: []\nconfig: {}\n", encoding="utf-8")

    calls: list[tuple[list[str], dict]] = []

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
        cameras="",
        extra_args="--max-events 5",
    )

    mod.cmd_start(args)

    assert len(calls) == 1
    cmd, env = calls[0]
    assert "--graph" in cmd
    assert str(graph) in cmd
    assert "--camera-id" not in cmd
    assert env["SS_CAMERA_ID"] == "cam01"
    assert env["SS_SOURCE_TYPE"] == "rtsp"
    assert env["SS_SOURCE_URL"] == "rtsp://127.0.0.1:8554/stream1"
