from __future__ import annotations

import importlib.util
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
    monkeypatch.setattr(mod, "run_cmd", lambda _cmd, *, cwd, dry_run: 0)
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
