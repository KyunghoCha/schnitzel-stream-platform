from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_scaffold_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "scaffold_plugin.py"
    spec = importlib.util.spec_from_file_location("scaffold_plugin_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_scaffold_generates_node_plugin_files(tmp_path: Path):
    mod = _load_scaffold_module()
    rc = mod.run(
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

    plugin = tmp_path / "src" / "schnitzel_stream" / "packs" / "sensor" / "nodes" / "threshold_node.py"
    test_file = tmp_path / "tests" / "unit" / "packs" / "sensor" / "nodes" / "test_threshold_node.py"
    graph = tmp_path / "configs" / "graphs" / "dev_sensor_threshold_node_v2.yaml"
    exports = tmp_path / "src" / "schnitzel_stream" / "packs" / "sensor" / "nodes" / "__init__.py"

    assert plugin.exists()
    assert test_file.exists()
    assert graph.exists()
    assert exports.exists()

    plugin_text = plugin.read_text(encoding="utf-8")
    assert "class ThresholdNode" in plugin_text
    assert "Intent:" in plugin_text

    graph_text = graph.read_text(encoding="utf-8")
    assert "schnitzel_stream.packs.sensor.nodes.threshold_node:ThresholdNode" in graph_text
    exports_text = exports.read_text(encoding="utf-8")
    assert "from .threshold_node import ThresholdNode" in exports_text
    assert '"ThresholdNode"' in exports_text


def test_scaffold_refuses_overwrite_without_force(tmp_path: Path):
    mod = _load_scaffold_module()
    args = [
        "--repo-root",
        str(tmp_path),
        "--pack",
        "audio",
        "--kind",
        "sink",
        "--name",
        "AudioSink",
    ]
    assert mod.run(args) == 0
    assert mod.run(args) == 1


def test_scaffold_force_overwrites_existing_files(tmp_path: Path):
    mod = _load_scaffold_module()
    args = [
        "--repo-root",
        str(tmp_path),
        "--pack",
        "robotics",
        "--kind",
        "source",
        "--name",
        "TelemetrySource",
    ]
    assert mod.run(args) == 0

    plugin = tmp_path / "src" / "schnitzel_stream" / "packs" / "robotics" / "nodes" / "telemetry_source.py"
    exports = tmp_path / "src" / "schnitzel_stream" / "packs" / "robotics" / "nodes" / "__init__.py"
    plugin.write_text("# manual edit\n", encoding="utf-8")

    assert mod.run([*args, "--force"]) == 0
    assert "class TelemetrySource" in plugin.read_text(encoding="utf-8")
    exports_text = exports.read_text(encoding="utf-8")
    assert exports_text.count("from .telemetry_source import TelemetrySource") == 1
    assert exports_text.count('"TelemetrySource"') == 1


def test_scaffold_can_skip_export_registration(tmp_path: Path):
    mod = _load_scaffold_module()
    args = [
        "--repo-root",
        str(tmp_path),
        "--pack",
        "audio",
        "--kind",
        "source",
        "--name",
        "MicSource",
        "--no-register-export",
    ]
    assert mod.run(args) == 0
    exports = tmp_path / "src" / "schnitzel_stream" / "packs" / "audio" / "nodes" / "__init__.py"
    assert not exports.exists()


def test_scaffold_dry_run_prints_plan_without_writes(tmp_path: Path, capsys):
    mod = _load_scaffold_module()
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--kind",
            "node",
            "--name",
            "ThresholdNode",
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "action=create" in out
    assert "threshold_node.py" in out
    plugin = tmp_path / "src" / "schnitzel_stream" / "packs" / "sensor" / "nodes" / "threshold_node.py"
    assert not plugin.exists()


def test_scaffold_dry_run_returns_conflict_when_target_exists(tmp_path: Path, capsys):
    mod = _load_scaffold_module()
    args = [
        "--repo-root",
        str(tmp_path),
        "--pack",
        "sensor",
        "--kind",
        "node",
        "--name",
        "ThresholdNode",
    ]
    assert mod.run(args) == 0
    rc = mod.run([*args, "--dry-run"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "action=conflict" in out


def test_scaffold_rejects_dry_run_validate_generated_combo(tmp_path: Path, capsys):
    mod = _load_scaffold_module()
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--kind",
            "node",
            "--name",
            "ThresholdNode",
            "--dry-run",
            "--validate-generated",
        ]
    )
    assert rc == 2
    assert "--dry-run cannot be combined with --validate-generated" in capsys.readouterr().err


def test_scaffold_validate_generated_runs_post_validation(tmp_path: Path, monkeypatch):
    mod = _load_scaffold_module()
    captured: dict[str, Path] = {}

    def _fake_validate(*, paths, repo_root, current_repo_root):
        captured["repo_root"] = repo_root
        captured["current_repo_root"] = current_repo_root
        return mod.PostGenerateValidation(ok=True, command="validate", returncode=0, stdout_tail="", stderr_tail="")

    monkeypatch.setattr(mod, "_run_post_generate_validation", _fake_validate)
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--kind",
            "node",
            "--name",
            "ThresholdNode",
            "--validate-generated",
        ]
    )
    assert rc == 0
    assert captured["repo_root"] == tmp_path.resolve()
    assert captured["current_repo_root"] == Path(mod.__file__).resolve().parents[1]


def test_scaffold_validate_generated_failure_keeps_generated_files(tmp_path: Path, monkeypatch):
    mod = _load_scaffold_module()

    def _failed_validate(*, paths, repo_root, current_repo_root):
        return mod.PostGenerateValidation(
            ok=False,
            command="validate",
            returncode=1,
            stdout_tail="",
            stderr_tail="failure",
        )

    monkeypatch.setattr(mod, "_run_post_generate_validation", _failed_validate)
    rc = mod.run(
        [
            "--repo-root",
            str(tmp_path),
            "--pack",
            "sensor",
            "--kind",
            "node",
            "--name",
            "ThresholdNode",
            "--validate-generated",
        ]
    )
    assert rc == 1
    plugin = tmp_path / "src" / "schnitzel_stream" / "packs" / "sensor" / "nodes" / "threshold_node.py"
    graph = tmp_path / "configs" / "graphs" / "dev_sensor_threshold_node_v2.yaml"
    assert plugin.exists()
    assert graph.exists()


def test_scaffold_validation_env_contains_repo_root_src_first(tmp_path: Path):
    mod = _load_scaffold_module()
    env = mod._build_validation_env(repo_root=tmp_path.resolve(), current_repo_root=Path(mod.__file__).resolve().parents[1])
    parts = [p for p in str(env.get("PYTHONPATH", "")).split(mod.os.pathsep) if p]
    assert parts[0] == str((tmp_path / "src").resolve())
    assert parts[1] == str((Path(mod.__file__).resolve().parents[1] / "src").resolve())
