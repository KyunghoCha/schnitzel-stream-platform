from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def test_cli_validate_only_default_graph():
    root = Path(__file__).resolve().parents[2]

    cmd = [sys.executable, "-m", "schnitzel_stream", "validate"]
    result = subprocess.run(cmd, cwd=str(root / "src"), check=True)
    assert result.returncode == 0


def test_cli_default_graph_is_v2():
    from schnitzel_stream.cli.__main__ import _default_graph_path
    from schnitzel_stream.graph.spec import peek_graph_version

    assert peek_graph_version(_default_graph_path()) == 2


def test_cli_validate_only_v2_graph_spec_without_version(tmp_path):
    root = Path(__file__).resolve().parents[2]
    p = tmp_path / "graph.yaml"
    p.write_text(
        textwrap.dedent(
            """
            nodes:
              - id: src
                kind: source
                plugin: schnitzel_stream.nodes.dev:StaticSource
                config:
                  packets: []
              - id: sink
                kind: sink
                plugin: schnitzel_stream.nodes.dev:Identity
            edges:
              - from: src
                to: sink
            """
        ).lstrip(),
        encoding="utf-8",
    )

    cmd = [sys.executable, "-m", "schnitzel_stream", "validate", "--graph", str(p)]
    result = subprocess.run(cmd, cwd=str(root / "src"), check=True)
    assert result.returncode == 0


@pytest.mark.parametrize(
    "flag",
    [
        "--camera-id",
        "--video",
        "--source-type",
        "--camera-index",
        "--dry-run",
        "--output-jsonl",
        "--visualize",
        "--loop",
    ],
)
def test_cli_rejects_removed_legacy_flags(flag: str):
    root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "-m", "schnitzel_stream", flag]
    result = subprocess.run(cmd, cwd=str(root / "src"), capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "unrecognized arguments" in (result.stderr or "")
