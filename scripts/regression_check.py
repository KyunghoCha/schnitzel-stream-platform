#!/usr/bin/env python3
# Docs: docs/implementation/80-testing/regression/spec.md
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "regression" / "golden_events.jsonl"
TMP_OUT = Path(tempfile.gettempdir()) / "events_regression.jsonl"


_COMPARE_KEYS = {"event_type", "object_type", "severity", "track_id", "bbox", "confidence", "zone"}


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in _COMPARE_KEYS}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _run_pipeline(max_events: int) -> None:
    env = os.environ.copy()
    # 회귀 검증은 runtime default(real)와 분리해 mock 모드를 명시적으로 고정한다.
    env["AI_MODEL_MODE"] = "mock"
    snap_dir = str(Path(tempfile.gettempdir()) / "snapshots_regression")
    env["AI_EVENTS_SNAPSHOT_BASE_DIR"] = snap_dir
    env["AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX"] = snap_dir

    cmd = [
        sys.executable,
        "-m",
        "schnitzel_stream",
        "--output-jsonl",
        str(TMP_OUT),
        "--max-events",
        str(max_events),
    ]
    subprocess.run(cmd, cwd=str(ROOT / "src"), env=env, check=True)


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
