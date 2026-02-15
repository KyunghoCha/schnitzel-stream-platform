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

    assert plugin.exists()
    assert test_file.exists()
    assert graph.exists()

    plugin_text = plugin.read_text(encoding="utf-8")
    assert "class ThresholdNode" in plugin_text
    assert "Intent:" in plugin_text

    graph_text = graph.read_text(encoding="utf-8")
    assert "schnitzel_stream.packs.sensor.nodes.threshold_node:ThresholdNode" in graph_text


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
    plugin.write_text("# manual edit\n", encoding="utf-8")

    assert mod.run([*args, "--force"]) == 0
    assert "class TelemetrySource" in plugin.read_text(encoding="utf-8")
