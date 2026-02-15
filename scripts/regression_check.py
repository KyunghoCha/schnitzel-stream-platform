#!/usr/bin/env python3
# Docs: docs/implementation/80-testing/regression/spec.md
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from schnitzel_stream.control.throttle import FixedBudgetThrottle
from schnitzel_stream.graph.spec import load_node_graph_spec
from schnitzel_stream.runtime.inproc import InProcGraphRunner

GOLDEN = ROOT / "tests" / "regression" / "v2_golden_events.jsonl"
TMP_OUT = Path(tempfile.gettempdir()) / "events_regression.jsonl"
GRAPH = ROOT / "configs" / "graphs" / "dev_vision_e2e_mock_v2.yaml"


_COMPARE_KEYS = {"event_type", "object_type", "severity", "track_id", "bbox", "confidence", "zone"}


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in _COMPARE_KEYS}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _run_pipeline(max_events: int) -> None:
    spec = load_node_graph_spec(GRAPH)
    runner = InProcGraphRunner()
    throttle = FixedBudgetThrottle(max_source_emits_total=max_events) if max_events > 0 else None
    result = runner.run(nodes=spec.nodes, edges=spec.edges, throttle=throttle)

    # Intent: for v2 golden checks we persist forwarded packets from terminal node `out`.
    outs = result.outputs_by_node.get("out", [])
    lines: list[str] = []
    for packet in outs:
        if isinstance(packet.payload, dict):
            lines.append(json.dumps(packet.payload, ensure_ascii=False))
    TMP_OUT.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _compare(golden: list[dict[str, Any]], current: list[dict[str, Any]]) -> tuple[bool, str]:
    g_norm = [_normalize(p) for p in golden]
    c_norm = [_normalize(p) for p in current]

    if g_norm == c_norm:
        return True, "OK"

    # 기본 diff 요약
    msg = []
    msg.append(f"golden_count={len(g_norm)} current_count={len(c_norm)}")
    for i, (g, c) in enumerate(zip(g_norm, c_norm)):
        if g != c:
            msg.append(f"mismatch_at_index={i}")
            msg.append(f"golden={g}")
            msg.append(f"current={c}")
            break
    return False, "\n".join(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Regression check for pipeline output")
    parser.add_argument("--max-events", type=int, default=5)
    parser.add_argument("--update-golden", action="store_true")
    args = parser.parse_args()

    if TMP_OUT.exists():
        TMP_OUT.unlink()

    _run_pipeline(args.max_events)
    current = _load_jsonl(TMP_OUT)

    if args.update_golden:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(TMP_OUT.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"updated_golden={GOLDEN}")
        return 0

    if not GOLDEN.exists():
        print(f"missing_golden={GOLDEN}")
        return 2

    golden = _load_jsonl(GOLDEN)
    ok, detail = _compare(golden, current)
    if ok:
        print("regression_ok")
        return 0
    print("regression_failed")
    print(detail)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
