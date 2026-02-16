from __future__ import annotations

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


def test_multi_cam_delegates_to_stream_fleet(monkeypatch, capsys):
    mod = _load_multi_cam_module()
    observed: dict[str, object] = {}

    def _fake_run(argv=None, **kwargs):
        observed["argv"] = list(argv or [])
        observed["kwargs"] = dict(kwargs)
        return 7

    monkeypatch.setattr(mod.stream_fleet, "run", _fake_run)
    code = mod.run(["status", "--log-dir", "/tmp/demo"])
    assert code == 7
    assert observed["argv"] == ["status", "--log-dir", "/tmp/demo"]
    kwargs = observed["kwargs"]
    assert kwargs["prog"] == "multi_cam"
    assert kwargs["default_config"].endswith("configs/cameras.yaml")
    assert kwargs["default_graph_template"].endswith("configs/graphs/dev_camera_template_v2.yaml")
    assert kwargs["default_log_dir"].endswith("ai_pipeline_multi_cam_run")

    err = capsys.readouterr().err
    assert "legacy alias" in err.lower()
