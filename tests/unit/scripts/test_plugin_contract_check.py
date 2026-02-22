from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _load_script_module(*, name: str, rel_path: str) -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / rel_path
    spec = importlib.util.spec_from_file_location(name, mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_scaffold_module() -> ModuleType:
    return _load_script_module(name="scaffold_plugin_for_contract_tests", rel_path="scripts/scaffold_plugin.py")


def _load_contract_module() -> ModuleType:
    return _load_script_module(name="plugin_contract_check_test_module", rel_path="scripts/plugin_contract_check.py")


def _scaffold_sensor_pack(tmp_path: Path) -> None:
    scaffold = _load_scaffold_module()
    rc = scaffold.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--kind",
            "node",
            "--name",
            "ThresholdNode",
        ]
    )
    assert rc == 0


def test_plugin_contract_check_usage_error_when_class_without_module(tmp_path: Path, capsys):
    mod = _load_contract_module()
    rc = mod.run(["--repo-root", str(tmp_path), "--pack", "sensor", "--class", "ThresholdNode"])
    assert rc == 2
    assert "--class requires --module" in capsys.readouterr().err


def test_plugin_contract_check_fails_when_pack_missing(tmp_path: Path):
    mod = _load_contract_module()
    rc = mod.run(["--repo-root", str(tmp_path), "--pack", "sensor", "--json"])
    assert rc == 1


def test_plugin_contract_check_strict_success_for_scaffolded_pack(tmp_path: Path, capsys):
    _scaffold_sensor_pack(tmp_path)
    capsys.readouterr()
    mod = _load_contract_module()
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--module",
            "threshold_node",
            "--class",
            "ThresholdNode",
            "--strict",
            "--json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert payload["errors"] == []


def test_plugin_contract_check_graph_validate_success_with_stubbed_subprocess(tmp_path: Path, monkeypatch, capsys):
    _scaffold_sensor_pack(tmp_path)
    capsys.readouterr()
    mod = _load_contract_module()

    def _ok_subprocess(*, cmd, cwd, env):
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod, "_run_subprocess", _ok_subprocess)

    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--module",
            "threshold_node",
            "--class",
            "ThresholdNode",
            "--graph",
            str(tmp_path / "configs" / "graphs" / "dev_sensor_threshold_node_v2.yaml"),
            "--json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out.strip())
    checks = {row["id"]: row for row in payload["checks"]}
    assert checks["graph.validate"]["ok"] is True


def test_plugin_contract_check_strict_detects_missing_export(tmp_path: Path, capsys):
    _scaffold_sensor_pack(tmp_path)
    capsys.readouterr()
    init_file = tmp_path / "src" / "schnitzel_stream" / "packs" / "sensor" / "nodes" / "__init__.py"
    init_file.write_text("from __future__ import annotations\n\n__all__ = []\n", encoding="utf-8")

    mod = _load_contract_module()
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--module",
            "threshold_node",
            "--class",
            "ThresholdNode",
            "--strict",
            "--json",
        ]
    )
    assert rc == 1
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["status"] == "failed"
    assert any("strict.module.export" in err or "init.import" in err for err in payload["errors"])
