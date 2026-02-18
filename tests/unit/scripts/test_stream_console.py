from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_stream_console_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "stream_console.py"
    spec = importlib.util.spec_from_file_location("stream_console_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_status_json_schema(monkeypatch, capsys):
    mod = _load_stream_console_module()
    monkeypatch.setattr(
        mod.console_ops,
        "collect_status",
        lambda **_kwargs: {
            "schema_version": 1,
            "ready": True,
            "log_dir": "x",
            "api": {"status": "running", "running": True, "port_open": True, "health": {"reason": "ok", "status_code": 200}},
            "ui": {"status": "running", "running": True, "port_open": True},
        },
    )
    rc = mod.run(["status", "--json"])
    assert rc == mod.EXIT_OK

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["schema_version"] == 1
    assert payload["ready"] is True


def test_down_is_idempotent(monkeypatch, capsys):
    mod = _load_stream_console_module()
    monkeypatch.setattr(
        mod.console_ops,
        "stop_all_services",
        lambda **_kwargs: [
            {"service": "api", "action": "not_found", "pid": None},
            {"service": "ui", "action": "not_found", "pid": None},
        ],
    )
    rc = mod.run(["down"])
    assert rc == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "api: not_found" in out
    assert "ui: not_found" in out


def test_up_passes_allow_local_mutations_and_token(monkeypatch):
    mod = _load_stream_console_module()
    observed: dict[str, object] = {}

    def _fake_start(**kwargs):
        observed["allow_local_mutations"] = kwargs["allow_local_mutations"]
        observed["token"] = kwargs["token"]
        observed["api_only"] = kwargs["api_only"]
        observed["ui_only"] = kwargs["ui_only"]
        return [{"service": "api", "action": "started", "pid": 123}]

    monkeypatch.setattr(mod.console_ops, "start_selected_services", _fake_start)
    monkeypatch.setattr(
        mod.console_ops,
        "collect_status",
        lambda **_kwargs: {
            "schema_version": 1,
            "ready": True,
            "log_dir": "x",
            "api": {"status": "running", "running": True, "port_open": True, "health": {"reason": "ok", "status_code": 200}},
            "ui": {"status": "not_found", "running": False, "port_open": False},
        },
    )

    rc = mod.run(["up", "--allow-local-mutations", "--token", "secret", "--api-only"])
    assert rc == mod.EXIT_OK
    assert observed["allow_local_mutations"] is True
    assert observed["token"] == "secret"
    assert observed["api_only"] is True
    assert observed["ui_only"] is False


def test_doctor_strict_fails_when_required_missing(monkeypatch):
    mod = _load_stream_console_module()
    check = mod.env_ops.CheckResult(name="fastapi", required=True, ok=False, detail="missing")
    monkeypatch.setattr(mod.env_ops, "run_checks", lambda **_kwargs: [check])
    rc = mod.run(["doctor", "--strict"])
    assert rc == mod.EXIT_RUNTIME


def test_up_returns_usage_for_invalid_port():
    mod = _load_stream_console_module()
    rc = mod.run(["up", "--api-port", "0"])
    assert rc == mod.EXIT_USAGE


def test_up_failure_reports_dependency_guidance(monkeypatch, capsys):
    mod = _load_stream_console_module()
    monkeypatch.setattr(
        mod.console_ops,
        "start_selected_services",
        lambda **_kwargs: [{"service": "api", "action": "started", "pid": 123}],
    )
    monkeypatch.setattr(
        mod,
        "_wait_for_ready",
        lambda **_kwargs: {
            "schema_version": 1,
            "ready": False,
            "log_dir": "x",
            "state": {"api": {"enabled": True}, "ui": {"enabled": False}},
            "api": {"status": "stale", "running": False, "port_open": False, "health": {"reason": "n/a", "status_code": None}},
            "ui": {"status": "not_found", "running": False, "port_open": False},
        },
    )
    check = mod.env_ops.CheckResult(name="fastapi", required=True, ok=False, detail="missing")
    monkeypatch.setattr(mod.env_ops, "run_checks", lambda **_kwargs: [check])

    rc = mod.run(["up", "--api-only"])
    assert rc == mod.EXIT_RUNTIME
    err = capsys.readouterr().err
    assert "failure_kind=dependency_missing" in err
    assert "recover_powershell=" in err
    assert "recover_bash=" in err


def test_up_failure_reports_port_conflict_guidance(monkeypatch, capsys):
    mod = _load_stream_console_module()
    monkeypatch.setattr(
        mod.console_ops,
        "start_selected_services",
        lambda **_kwargs: [{"service": "api", "action": "started", "pid": 123}],
    )
    monkeypatch.setattr(
        mod,
        "_wait_for_ready",
        lambda **_kwargs: {
            "schema_version": 1,
            "ready": False,
            "log_dir": "x",
            "state": {"api": {"enabled": True}, "ui": {"enabled": False}},
            "api": {"status": "stale", "running": False, "port_open": True, "health": {"reason": "n/a", "status_code": None}},
            "ui": {"status": "not_found", "running": False, "port_open": False},
        },
    )
    monkeypatch.setattr(mod.env_ops, "run_checks", lambda **_kwargs: [])

    rc = mod.run(["up", "--api-only", "--api-port", "18700"])
    assert rc == mod.EXIT_RUNTIME
    err = capsys.readouterr().err
    assert "failure_kind=port_conflict" in err
    assert "failure_reason=api port 18700 is already in use" in err


def test_up_failure_reports_api_health_failed(monkeypatch, capsys):
    mod = _load_stream_console_module()
    monkeypatch.setattr(
        mod.console_ops,
        "start_selected_services",
        lambda **_kwargs: [{"service": "api", "action": "started", "pid": 123}],
    )
    monkeypatch.setattr(
        mod,
        "_wait_for_ready",
        lambda **_kwargs: {
            "schema_version": 1,
            "ready": False,
            "log_dir": "x",
            "state": {"api": {"enabled": True}, "ui": {"enabled": False}},
            "api": {
                "status": "running",
                "running": True,
                "port_open": False,
                "health": {"ok": False, "reason": "http 500", "status_code": 500},
            },
            "ui": {"status": "not_found", "running": False, "port_open": False},
        },
    )
    monkeypatch.setattr(mod.env_ops, "run_checks", lambda **_kwargs: [])

    rc = mod.run(["up", "--api-only"])
    assert rc == mod.EXIT_RUNTIME
    err = capsys.readouterr().err
    assert "failure_kind=api_health_failed" in err
    assert "failure_reason=http 500" in err
