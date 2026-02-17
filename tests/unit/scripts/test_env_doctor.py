from __future__ import annotations

import importlib.util
import json
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path


def _load_env_doctor_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "env_doctor.py"
    spec = importlib.util.spec_from_file_location("env_doctor_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_env_doctor_strict_fails_when_required_missing(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 9))

    def _fake_import(name: str):
        if name == "omegaconf":
            raise ModuleNotFoundError("No module named omegaconf")
        return object()

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run(["--strict"])
    assert rc == 1


def test_env_doctor_non_strict_allows_required_missing(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 2))

    def _fake_import(_name: str):
        raise ModuleNotFoundError("missing")

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run([])
    assert rc == 0


def test_env_doctor_json_payload(monkeypatch, capsys):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 8))

    def _fake_import(name: str):
        if name == "cv2":
            raise ModuleNotFoundError("No module named cv2")
        return object()

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run(["--json", "--strict"])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["tool"] == "env_doctor"
    assert payload["status"] == "ok"
    assert payload["summary"]["required_failed"] == 0
    assert payload["summary"]["optional_failed"] == 1


def test_env_doctor_fails_for_low_python_in_strict(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 10, 14))
    monkeypatch.setattr(mod.importlib, "import_module", lambda _name: object())
    rc = mod.run(["--strict"])
    assert rc == 1


def test_env_doctor_yolo_profile_requires_ultralytics(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 10))

    def _fake_import(name: str):
        if name == "ultralytics":
            raise ModuleNotFoundError("No module named ultralytics")
        if name == "torch":
            fake_torch = SimpleNamespace(
                cuda=SimpleNamespace(is_available=lambda: False, device_count=lambda: 0),
                version=SimpleNamespace(cuda=None),
            )
            return fake_torch
        return object()

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run(["--strict", "--profile", "yolo"])
    assert rc == 1


def test_env_doctor_webcam_profile_probe_is_optional(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 10))

    class _FakeCap:
        def isOpened(self):
            return False

        def release(self):
            return None

    class _FakeCv2:
        def VideoCapture(self, _index):
            return _FakeCap()

    def _fake_import(name: str):
        if name == "cv2":
            return _FakeCv2()
        return object()

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run(["--strict", "--profile", "webcam", "--probe-webcam", "--camera-index", "0"])
    # webcam probe is warning-only by design.
    assert rc == 0


def test_env_doctor_yolo_profile_json_includes_profile(monkeypatch, capsys):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 10))

    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: True, device_count=lambda: 1),
        version=SimpleNamespace(cuda="12.1"),
    )

    def _fake_import(name: str):
        if name == "torch":
            return fake_torch
        return object()

    monkeypatch.setattr(mod.importlib, "import_module", _fake_import)
    rc = mod.run(["--json", "--strict", "--profile", "yolo", "--model-path", "models/yolov8n.pt"])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["profile"] == "yolo"
    check_names = {item["name"] for item in payload["checks"]}
    assert "torch_cuda" in check_names
    assert "yolo_model_path" in check_names


def test_env_doctor_console_profile_requires_node_npm(monkeypatch):
    mod = _load_env_doctor_module()
    monkeypatch.setattr(mod, "_python_version_info", lambda: (3, 11, 10))
    monkeypatch.setattr(mod.importlib, "import_module", lambda _name: object())
    monkeypatch.setattr(mod.env_ops.shutil, "which", lambda _name: None)
    rc = mod.run(["--strict", "--profile", "console"])
    assert rc == 1
