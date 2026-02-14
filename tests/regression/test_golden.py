from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "regression" / "golden_events.jsonl"
LEGACY_GRAPH = ROOT / "configs" / "graphs" / "legacy_pipeline.yaml"


_COMPARE_KEYS = {"event_type", "object_type", "severity", "track_id", "bbox", "confidence", "zone"}


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in _COMPARE_KEYS}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_golden_regression(tmp_path):
    if not GOLDEN.exists():
        pytest.skip(f"golden file not found: {GOLDEN}")

    out_file = tmp_path / "events_regression_test.jsonl"

    env = os.environ.copy()
    # 회귀 테스트는 mock 경로를 명시적으로 사용한다.
    env["AI_MODEL_MODE"] = "mock"
    env["AI_EVENTS_SNAPSHOT_BASE_DIR"] = str(tmp_path / "snapshots")
    env["AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX"] = str(tmp_path / "snapshots")

    cmd = [
        sys.executable,
        "-m",
        "schnitzel_stream",
        "--graph",
        str(LEGACY_GRAPH),
        "--output-jsonl",
        str(out_file),
        "--max-events",
        "5",
    ]
    subprocess.run(cmd, cwd=str(ROOT / "src"), env=env, check=True)

    golden = _load_jsonl(GOLDEN)
    current = _load_jsonl(out_file)

    g_norm = [_normalize(p) for p in golden]
    c_norm = [_normalize(p) for p in current]

    assert g_norm == c_norm
