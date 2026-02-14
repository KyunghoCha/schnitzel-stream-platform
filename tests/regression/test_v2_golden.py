from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from schnitzel_stream.graph.spec import load_node_graph_spec
from schnitzel_stream.runtime.inproc import InProcGraphRunner

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "regression" / "v2_golden_events.jsonl"
GRAPH = ROOT / "configs" / "graphs" / "dev_cctv_e2e_mock_v2.yaml"

_COMPARE_KEYS = {"event_type", "object_type", "severity", "track_id", "bbox", "confidence", "zone"}


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in _COMPARE_KEYS}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_v2_golden_regression():
    if not GOLDEN.exists():
        pytest.skip(f"golden file not found: {GOLDEN}")
    if not GRAPH.exists():
        pytest.skip(f"graph file not found: {GRAPH}")

    spec = load_node_graph_spec(GRAPH)
    runner = InProcGraphRunner()
    result = runner.run(nodes=spec.nodes, edges=spec.edges)

    outs = result.outputs_by_node.get("out", [])
    current = []
    for pkt in outs:
        if not isinstance(pkt.payload, dict):
            continue
        current.append(pkt.payload)

    golden = _load_jsonl(GOLDEN)
    assert [_normalize(p) for p in current] == [_normalize(p) for p in golden]

