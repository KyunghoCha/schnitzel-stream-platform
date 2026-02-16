from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace


def _load_proc_graph_validate_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "proc_graph_validate.py"
    spec = importlib.util.spec_from_file_location("proc_graph_validate_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_proc_graph_validate_run_success_human_output(monkeypatch, capsys):
    mod = _load_proc_graph_validate_module()

    def _ok(_spec):
        return SimpleNamespace(
            spec_path="/tmp/spec.yaml",
            process_count=2,
            channel_count=1,
            link_count=1,
            resolved_process_graphs={"enqueue": "/tmp/enqueue.yaml", "drain": "/tmp/drain.yaml"},
            resolved_channel_paths={"q_main": "/tmp/queue.sqlite3"},
        )

    monkeypatch.setattr(mod, "_load_validator_api", lambda: (ValueError, _ok))
    rc = mod.run(["--spec", "configs/process_graphs/dev_durable_pair_pg_v1.yaml"])
    out = capsys.readouterr().out

    assert rc == mod.EXIT_OK
    assert "process graph validation ok" in out
    assert "processes=2 channels=1 links=1" in out


def test_proc_graph_validate_run_success_json_output(monkeypatch, capsys):
    mod = _load_proc_graph_validate_module()

    def _ok(_spec):
        return SimpleNamespace(
            spec_path="/tmp/spec.yaml",
            process_count=2,
            channel_count=1,
            link_count=1,
            resolved_process_graphs={"enqueue": "/tmp/enqueue.yaml"},
            resolved_channel_paths={"q_main": "/tmp/queue.sqlite3"},
        )

    monkeypatch.setattr(mod, "_load_validator_api", lambda: (ValueError, _ok))
    rc = mod.run(["--spec", "x.yaml", "--report-json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == mod.EXIT_OK
    assert payload["status"] == "ok"
    assert payload["process_count"] == 2


def test_proc_graph_validate_returns_validation_exit_code(monkeypatch, capsys):
    mod = _load_proc_graph_validate_module()

    class _ValidationError(Exception):
        pass

    def _fail(_spec):
        raise _ValidationError("bad process graph")

    monkeypatch.setattr(mod, "_load_validator_api", lambda: (_ValidationError, _fail))
    rc = mod.run(["--spec", "x.yaml"])
    err = capsys.readouterr().err

    assert rc == mod.EXIT_VALIDATION_ERROR
    assert "Validation failed:" in err


def test_proc_graph_validate_returns_general_exit_code(monkeypatch, capsys):
    mod = _load_proc_graph_validate_module()

    def _explode(_spec):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "_load_validator_api", lambda: (ValueError, _explode))
    rc = mod.run(["--spec", "x.yaml", "--report-json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == mod.EXIT_GENERAL_ERROR
    assert payload["status"] == "error"
    assert payload["error_kind"] == "runtime"


def test_proc_graph_validate_returns_general_exit_code_on_import_failure(monkeypatch, capsys):
    mod = _load_proc_graph_validate_module()

    def _boom_import():
        raise ModuleNotFoundError("omegaconf")

    monkeypatch.setattr(mod, "_load_validator_api", _boom_import)
    rc = mod.run(["--spec", "x.yaml", "--report-json"])
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert rc == mod.EXIT_GENERAL_ERROR
    assert payload["status"] == "error"
    assert payload["error_kind"] == "runtime"
