from __future__ import annotations

import importlib.util
import json
import sys
from types import ModuleType
from pathlib import Path


def _load_bootstrap_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "bootstrap_env.py"
    spec = importlib.util.spec_from_file_location("bootstrap_env_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bootstrap_console_dry_run_allows_missing_npm(monkeypatch):
    mod = _load_bootstrap_module()

    def _fake_which(name: str):
        if name == "npm":
            return None
        return "/usr/bin/python3"

    monkeypatch.setattr(mod, "_which", _fake_which)
    monkeypatch.setattr(mod, "run_cmd", lambda _cmd, *, cwd, dry_run, echo=True: 0)
    rc = mod.run(["--profile", "console", "--manager", "pip", "--dry-run"])
    assert rc == mod.EXIT_OK


def test_bootstrap_console_runtime_fails_when_npm_missing(monkeypatch):
    mod = _load_bootstrap_module()

    def _fake_which(name: str):
        if name == "npm":
            return None
        return "/usr/bin/python3"

    monkeypatch.setattr(mod, "_which", _fake_which)
    rc = mod.run(["--profile", "console", "--manager", "pip"])
    assert rc == mod.EXIT_RUNTIME


def test_bootstrap_json_envelope_contains_manager_selected(monkeypatch, capsys):
    mod = _load_bootstrap_module()
    monkeypatch.setattr(mod, "_which", lambda _name: "/usr/bin/ok")
    monkeypatch.setattr(mod, "run_cmd", lambda _cmd, *, cwd, dry_run, echo=True: 0)

    rc = mod.run(["--profile", "base", "--manager", "pip", "--dry-run", "--json"])
    assert rc == mod.EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert payload["manager_selected"] == "pip"
    assert payload["dry_run"] is True
    assert "next_action" in payload


def test_bootstrap_skip_doctor_marks_step_skipped(monkeypatch, capsys):
    mod = _load_bootstrap_module()
    seen_commands: list[list[str]] = []

    def _fake_run(cmd, *, cwd, dry_run, echo=True):
        seen_commands.append(list(cmd))
        return 0

    monkeypatch.setattr(mod, "_which", lambda _name: "/usr/bin/ok")
    monkeypatch.setattr(mod, "run_cmd", _fake_run)

    rc = mod.run(["--profile", "console", "--manager", "pip", "--dry-run", "--skip-doctor", "--json"])
    assert rc == mod.EXIT_OK
    payload = json.loads(capsys.readouterr().out.strip())
    assert any(step["name"] == "doctor" and step["status"] == "skipped" for step in payload["steps"])
    assert not any("env_doctor.py" in " ".join(cmd) for cmd in seen_commands)
