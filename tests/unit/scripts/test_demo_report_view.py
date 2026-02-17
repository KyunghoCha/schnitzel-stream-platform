from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_report_view_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "demo_report_view.py"
    spec = importlib.util.spec_from_file_location("demo_report_view_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_report(path: Path) -> None:
    payload = {
        "schema_version": 2,
        "profile": "ci",
        "status": "failed",
        "exit_code": 2,
        "scenarios": [
            {
                "id": "S1",
                "title": "inproc baseline",
                "status": "failed",
                "failure_kind": "environment",
                "failure_reason": "dependency_missing",
                "steps": [
                    {
                        "phase": "validate",
                        "stderr_tail": "ModuleNotFoundError: No module named 'omegaconf'",
                        "stdout_tail": "",
                    }
                ],
            }
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_report_view_generates_both_formats(tmp_path: Path):
    mod = _load_report_view_module()
    report_path = tmp_path / "reports" / "demo_pack_latest.json"
    _write_report(report_path)

    out_dir = tmp_path / "rendered"
    rc = mod.run(["--report", str(report_path), "--format", "both", "--out-dir", str(out_dir)])
    assert rc == 0

    md_path = out_dir / "demo_pack_latest.summary.md"
    html_path = out_dir / "demo_pack_latest.summary.html"
    assert md_path.exists()
    assert html_path.exists()
    md_text = md_path.read_text(encoding="utf-8")
    assert "Failure Reason" in md_text
    assert "dependency_missing" in md_text
    assert "dependency_missing" in html_path.read_text(encoding="utf-8")


def test_report_view_generates_md_only(tmp_path: Path):
    mod = _load_report_view_module()
    report_path = tmp_path / "demo.json"
    _write_report(report_path)

    rc = mod.run(["--report", str(report_path), "--format", "md"])
    assert rc == 0
    assert (tmp_path / "demo.summary.md").exists()
    assert not (tmp_path / "demo.summary.html").exists()


def test_report_view_fails_when_report_missing(tmp_path: Path):
    mod = _load_report_view_module()
    rc = mod.run(["--report", str(tmp_path / "missing.json"), "--format", "both"])
    assert rc == 1
