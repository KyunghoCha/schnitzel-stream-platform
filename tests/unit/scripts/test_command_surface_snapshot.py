from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def _load_command_surface_snapshot_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "command_surface_snapshot.py"
    spec = importlib.util.spec_from_file_location("command_surface_snapshot_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_command_surface_snapshot_has_stable_top_level_keys():
    mod = _load_command_surface_snapshot_module()
    payload = mod.build_snapshot()

    assert payload["schema_version"] == 1
    assert set(payload.keys()) == {
        "schema_version",
        "release_target",
        "freeze_scope",
        "version",
        "commands",
        "non_frozen_surfaces",
    }
    assert len(payload["commands"]) >= 8


def test_command_surface_snapshot_check_mode_passes(tmp_path: Path):
    mod = _load_command_surface_snapshot_module()
    payload = mod.build_snapshot()
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    rc = mod.run(["--check", "--baseline", str(baseline)])
    assert rc == 0


def test_command_surface_snapshot_check_mode_detects_drift(tmp_path: Path, capsys):
    mod = _load_command_surface_snapshot_module()
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"schema_version": 1}, ensure_ascii=False), encoding="utf-8")

    rc = mod.run(["--check", "--baseline", str(baseline), "--compact"])
    err = capsys.readouterr().err

    assert rc == 1
    assert "drift detected" in err
