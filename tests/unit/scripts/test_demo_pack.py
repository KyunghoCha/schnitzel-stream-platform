from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_demo_pack_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "demo_pack.py"
    spec = importlib.util.spec_from_file_location("demo_pack_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_showcase_graphs(repo_root: Path) -> None:
    graphs = repo_root / "configs" / "graphs"
    graphs.mkdir(parents=True, exist_ok=True)
    for name in (
        "showcase_inproc_v2.yaml",
        "showcase_durable_enqueue_v2.yaml",
        "showcase_durable_drain_ack_v2.yaml",
        "showcase_webcam_v2.yaml",
    ):
        (graphs / name).write_text("version: 2\nnodes: []\nedges: []\nconfig: {}\n", encoding="utf-8")


def test_build_scenarios_by_profile():
    mod = _load_demo_pack_module()
    repo_root = Path("/tmp/demo_pack_repo")

    ci_scenarios = mod._build_scenarios("ci", repo_root)
    assert [s.scenario_id for s in ci_scenarios] == ["S1", "S2"]
    assert all(not s.webcam_required for s in ci_scenarios)

    professor_scenarios = mod._build_scenarios("professor", repo_root)
    assert [s.scenario_id for s in professor_scenarios] == ["S1", "S2", "S3"]
    assert professor_scenarios[-1].webcam_required
    assert professor_scenarios[-1].graphs[0].name == "showcase_webcam_v2.yaml"


def test_run_writes_report_schema_for_ci(monkeypatch, tmp_path: Path):
    mod = _load_demo_pack_module()
    _write_showcase_graphs(tmp_path)
    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)

    def _ok_run(_cmd, *, cwd, env):
        assert cwd == tmp_path
        assert "PYTHONPATH" in env
        return mod.CommandResult(returncode=0, stdout="ok\n", stderr="", duration_sec=0.01)

    monkeypatch.setattr(mod, "_run_command", _ok_run)

    report_path = tmp_path / "outputs" / "reports" / "custom_demo_pack_report.json"
    rc = mod.run(["--profile", "ci", "--max-events", "5", "--report", str(report_path)])
    assert rc == 0
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["profile"] == "ci"
    assert payload["status"] == "ok"
    assert payload["exit_code"] == 0
    assert payload["summary"]["scenarios_total"] == 2
    assert payload["summary"]["scenarios_passed"] == 2
    assert payload["summary"]["scenarios_failed"] == 0
    assert len(payload["scenarios"]) == 2

    first_steps = payload["scenarios"][0]["steps"]
    assert first_steps[0]["phase"] == "validate"
    assert "schnitzel_stream" in first_steps[0]["command"]


def test_run_returns_2_on_validation_failure(monkeypatch, tmp_path: Path):
    mod = _load_demo_pack_module()
    _write_showcase_graphs(tmp_path)
    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)

    def _validate_fail(cmd, *, cwd, env):
        if "validate" in cmd:
            return mod.CommandResult(returncode=7, stdout="", stderr="invalid graph", duration_sec=0.01)
        return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)

    monkeypatch.setattr(mod, "_run_command", _validate_fail)

    report_path = tmp_path / "outputs" / "reports" / "validate_fail.json"
    rc = mod.run(["--profile", "ci", "--report", str(report_path)])
    assert rc == 2

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["exit_code"] == 2
    assert payload["scenarios"][0]["failure_kind"] == "validate"
    assert payload["scenarios"][0]["failure_reason"] == "validate_failed"


def test_run_returns_20_on_professor_webcam_failure(monkeypatch, tmp_path: Path):
    mod = _load_demo_pack_module()
    _write_showcase_graphs(tmp_path)
    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)

    def _webcam_fail(cmd, *, cwd, env):
        cmd_line = " ".join(cmd)
        if "validate" in cmd_line:
            return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)
        if "showcase_webcam_v2.yaml" in cmd_line:
            return mod.CommandResult(returncode=5, stdout="", stderr="camera open failed", duration_sec=0.01)
        return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)

    monkeypatch.setattr(mod, "_run_command", _webcam_fail)

    report_path = tmp_path / "outputs" / "reports" / "webcam_fail.json"
    rc = mod.run(["--profile", "professor", "--report", str(report_path)])
    assert rc == 20

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["exit_code"] == 20
    assert payload["summary"]["scenarios_total"] == 3
    assert payload["scenarios"][-1]["id"] == "S3"
    assert payload["scenarios"][-1]["failure_kind"] == "run"
    assert payload["scenarios"][-1]["failure_reason"] == "webcam_runtime_failed"


def test_run_returns_1_on_non_webcam_runtime_failure(monkeypatch, tmp_path: Path):
    mod = _load_demo_pack_module()
    _write_showcase_graphs(tmp_path)
    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)

    def _generic_run_fail(cmd, *, cwd, env):
        cmd_line = " ".join(cmd)
        if "validate" in cmd_line:
            return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)
        if "showcase_durable_drain_ack_v2.yaml" in cmd_line:
            return mod.CommandResult(returncode=9, stdout="", stderr="runtime failed", duration_sec=0.01)
        return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)

    monkeypatch.setattr(mod, "_run_command", _generic_run_fail)

    report_path = tmp_path / "outputs" / "reports" / "runtime_fail.json"
    rc = mod.run(["--profile", "ci", "--report", str(report_path)])
    assert rc == 1

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["exit_code"] == 1
    assert payload["scenarios"][-1]["id"] == "S2"
    assert payload["scenarios"][-1]["failure_kind"] == "run"
    assert payload["scenarios"][-1]["failure_reason"] == "runtime_failed"


def test_run_classifies_dependency_error_as_environment(monkeypatch, tmp_path: Path):
    mod = _load_demo_pack_module()
    _write_showcase_graphs(tmp_path)
    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)

    def _env_fail(cmd, *, cwd, env):
        cmd_line = " ".join(cmd)
        if "validate" in cmd_line:
            return mod.CommandResult(
                returncode=1,
                stdout="",
                stderr="ModuleNotFoundError: No module named 'omegaconf'",
                duration_sec=0.01,
            )
        return mod.CommandResult(returncode=0, stdout="ok", stderr="", duration_sec=0.01)

    monkeypatch.setattr(mod, "_run_command", _env_fail)

    report_path = tmp_path / "outputs" / "reports" / "env_fail.json"
    rc = mod.run(["--profile", "ci", "--report", str(report_path)])
    assert rc == 2

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["scenarios"][0]["failure_kind"] == "environment"
    assert payload["scenarios"][0]["failure_reason"] == "dependency_missing"
