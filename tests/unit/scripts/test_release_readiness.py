from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def _load_release_readiness_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "release_readiness.py"
    spec = importlib.util.spec_from_file_location("release_readiness_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_checks_lab_rc_contract():
    mod = _load_release_readiness_module()
    checks = mod._build_checks("lab-rc")

    check_ids = [c.check_id for c in checks]
    assert "compileall" in check_ids
    assert "command_surface_snapshot" in check_ids
    assert "ssot_sync_check" in check_ids


def test_run_json_success(monkeypatch, capsys):
    mod = _load_release_readiness_module()

    def _ok_run_one(*, spec, cwd):
        return mod.CheckResult(
            check_id=spec.check_id,
            category=spec.category,
            command=spec.command,
            returncode=0,
            duration_sec=0.01,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(mod, "_run_one", _ok_run_one)

    rc = mod.run(["--profile", "lab-rc", "--json"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == mod.EXIT_OK
    assert payload["profile"] == "lab-rc"
    assert payload["failed"] == 0
    assert payload["exit_code"] == 0


def test_run_json_failure(monkeypatch, capsys):
    mod = _load_release_readiness_module()

    def _mixed_run_one(*, spec, cwd):
        code = 1 if spec.check_id == "ssot_sync_check" else 0
        return mod.CheckResult(
            check_id=spec.check_id,
            category=spec.category,
            command=spec.command,
            returncode=code,
            duration_sec=0.02,
            stdout="",
            stderr="drift" if code else "",
        )

    monkeypatch.setattr(mod, "_run_one", _mixed_run_one)

    rc = mod.run(["--profile", "lab-rc", "--json"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == mod.EXIT_FAILED
    assert payload["failed"] == 1
    assert payload["exit_code"] == 1
    assert any(item["id"] == "ssot_sync_check" and item["status"] == "failed" for item in payload["checks"])


def test_run_invalid_profile_returns_usage(capsys):
    mod = _load_release_readiness_module()
    rc = mod.run(["--profile", "wrong"])
    err = capsys.readouterr().err

    assert rc == mod.EXIT_USAGE
    assert "--profile must be: lab-rc" in err
