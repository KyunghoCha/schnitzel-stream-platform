from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def test_cli_validate_only_v1_default_graph():
    root = Path(__file__).resolve().parents[2]

    cmd = [sys.executable, "-m", "schnitzel_stream", "validate"]
    result = subprocess.run(cmd, cwd=str(root / "src"), check=True)
    assert result.returncode == 0


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
