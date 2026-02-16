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
