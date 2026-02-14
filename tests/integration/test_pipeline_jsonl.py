from __future__ import annotations

# 파이프라인 통합 테스트 (jsonl 출력)

import json
import os
import subprocess
import sys
from pathlib import Path


def test_pipeline_jsonl_output(tmp_path):
    root = Path(__file__).resolve().parents[2]
    out_file = tmp_path / "events_test.jsonl"
    legacy_graph = root / "configs" / "graphs" / "legacy_pipeline.yaml"

    env = os.environ.copy()
    # 통합 테스트는 runtime default(real)와 분리해 mock 모드를 명시적으로 사용한다.
    env["AI_MODEL_MODE"] = "mock"
    env["AI_EVENTS_SNAPSHOT_BASE_DIR"] = str(tmp_path / "snapshots")
    env["AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX"] = str(tmp_path / "snapshots")

    cmd = [
        sys.executable,
        "-m",
        "schnitzel_stream",
        "--graph",
        str(legacy_graph),
        "--output-jsonl",
        str(out_file),
        "--max-events",
        "3",
    ]
    result = subprocess.run(cmd, cwd=str(root / "src"), env=env, check=True)
    assert result.returncode == 0

    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    sample = json.loads(lines[0])
    for key in ("event_id", "ts", "site_id", "camera_id", "event_type", "bbox", "zone"):
        assert key in sample
