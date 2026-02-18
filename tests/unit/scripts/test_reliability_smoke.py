from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_reliability_smoke_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "reliability_smoke.py"
    spec = importlib.util.spec_from_file_location("reliability_smoke_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_targets_for_mode_contract():
    mod = _load_reliability_smoke_module()
    quick = mod._targets_for_mode("quick")
    full = mod._targets_for_mode("full")
    assert "tests/unit/test_sqlite_queue.py" in quick
    assert "tests/integration/test_v2_durable_queue_idempotency_e2e.py" in full
    assert len(full) > len(quick)


def test_run_json_success(monkeypatch, capsys):
    mod = _load_reliability_smoke_module()

    def _ok_run(**_kwargs):
        return mod.SmokeResult(
            returncode=0,
            stdout="5 passed in 0.42s",
            stderr="",
            duration_sec=0.42,
        )

    monkeypatch.setattr(mod, "_run_pytest", _ok_run)
    rc = mod.run(["--mode", "quick", "--json"])
    assert rc == mod.EXIT_OK

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["schema_version"] == 1
    assert payload["mode"] == "quick"
    assert payload["tests_total"] == 5
    assert payload["passed"] == 5
    assert payload["failed"] == 0


def test_run_returns_runtime_on_failure(monkeypatch, capsys):
    mod = _load_reliability_smoke_module()

    def _failed_run(**_kwargs):
        return mod.SmokeResult(
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'pytest'",
            duration_sec=0.1,
        )

    monkeypatch.setattr(mod, "_run_pytest", _failed_run)
    rc = mod.run(["--mode", "quick", "--json"])
    assert rc == mod.EXIT_RUNTIME

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["failed"] == 1
    assert payload["returncode"] == 1


def test_run_returns_usage_on_invalid_mode(capsys):
    mod = _load_reliability_smoke_module()
    rc = mod.run(["--mode", "invalid"])
    assert rc == mod.EXIT_USAGE
    err = capsys.readouterr().err
    assert "--mode must be one of: quick, full" in err
