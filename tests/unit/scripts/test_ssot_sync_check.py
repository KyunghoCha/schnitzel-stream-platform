from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def _load_ssot_sync_check_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "ssot_sync_check.py"
    spec = importlib.util.spec_from_file_location("ssot_sync_check_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_doc(path: Path, step_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.name == "execution_roadmap.md":
        path.write_text(
            f"Current step id: `{step_id}`\nCurrent position: **Phase X (`{step_id}`)**\n- `{step_id}` something `NOW`\n",
            encoding="utf-8",
        )
        return
    path.write_text(f"Current step id: `{step_id}`\n", encoding="utf-8")


def _write_baseline(repo_root: Path) -> Path:
    baseline = repo_root / "configs" / "policy" / "ssot_sync_snapshot_v1.json"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "documents": {
            "execution_roadmap": "docs/roadmap/execution_roadmap.md",
            "current_status": "docs/progress/current_status.md",
            "prompt": "PROMPT.md",
            "prompt_core": "PROMPT_CORE.md",
            "owner_split": "docs/roadmap/owner_split_playbook.md",
        },
        "patterns": {
            "step_id": "Current step id[^`]*`(?P<step>[^`]+)`",
            "roadmap_current_position": "Current position:.*\\\\(`(?P<step>P[0-9.]+)`\\\\)",
        },
    }
    baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return baseline


def test_ssot_sync_check_strict_passes(monkeypatch, tmp_path: Path, capsys):
    mod = _load_ssot_sync_check_module()
    step = "P26.1"

    _write_doc(tmp_path / "docs" / "roadmap" / "execution_roadmap.md", step)
    _write_doc(tmp_path / "docs" / "progress" / "current_status.md", step)
    _write_doc(tmp_path / "PROMPT.md", step)
    _write_doc(tmp_path / "PROMPT_CORE.md", step)
    _write_doc(tmp_path / "docs" / "roadmap" / "owner_split_playbook.md", step)
    baseline = _write_baseline(tmp_path)

    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(mod, "DEFAULT_BASELINE", str(baseline.relative_to(tmp_path)))

    rc = mod.run(["--strict", "--json"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == 0
    assert payload["status"] == "ok"
    assert payload["step_id"] == step


def test_ssot_sync_check_detects_step_mismatch(monkeypatch, tmp_path: Path, capsys):
    mod = _load_ssot_sync_check_module()

    _write_doc(tmp_path / "docs" / "roadmap" / "execution_roadmap.md", "P26.1")
    _write_doc(tmp_path / "docs" / "progress" / "current_status.md", "P26.2")
    _write_doc(tmp_path / "PROMPT.md", "P26.1")
    _write_doc(tmp_path / "PROMPT_CORE.md", "P26.1")
    _write_doc(tmp_path / "docs" / "roadmap" / "owner_split_playbook.md", "P26.1")
    baseline = _write_baseline(tmp_path)

    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(mod, "DEFAULT_BASELINE", str(baseline.relative_to(tmp_path)))

    rc = mod.run(["--strict", "--json"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == 1
    assert payload["status"] == "drift"
    assert any("step.consensus" in err for err in payload["errors"])


def test_ssot_sync_check_missing_baseline_is_usage(monkeypatch, tmp_path: Path, capsys):
    mod = _load_ssot_sync_check_module()

    monkeypatch.setattr(mod, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(mod, "DEFAULT_BASELINE", "configs/policy/missing.json")

    rc = mod.run(["--json"])
    err = capsys.readouterr().err

    assert rc == 2
    assert "baseline not found" in err
