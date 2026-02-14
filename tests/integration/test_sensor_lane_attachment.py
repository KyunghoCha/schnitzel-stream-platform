from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_pipeline_attaches_sensor_payload_when_enabled(tmp_path):
    root = Path(__file__).resolve().parents[2]
    out_file = tmp_path / "events_sensor.jsonl"
    legacy_graph = root / "configs" / "graphs" / "legacy_pipeline.yaml"

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["AI_MODEL_MODE"] = "mock"
    env["AI_SENSOR_ENABLED"] = "true"
    env["AI_SENSOR_TYPE"] = "ultrasonic"
    env["AI_SENSOR_ADAPTER"] = "ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource"
    env["AI_SENSOR_TIME_WINDOW_MS"] = "5000"
    env["AI_FAKE_SENSOR_INTERVAL_SEC"] = "0.01"

    cmd = [
        sys.executable,
        "-m",
        "schnitzel_stream",
        "--graph",
        str(legacy_graph),
        "--output-jsonl",
        str(out_file),
        "--max-events",
        "8",
    ]
    result = subprocess.run(cmd, cwd=str(root), env=env, check=True)
    assert result.returncode == 0

    payloads = [
        json.loads(line)
        for line in out_file.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]
    assert payloads
    sensor_payloads = [p.get("sensor") for p in payloads if p.get("sensor") is not None]
    assert sensor_payloads, "expected at least one event with attached sensor payload"
    first = sensor_payloads[0]
    assert first["sensor_id"] == env.get("AI_FAKE_SENSOR_ID", "ultrasonic-front-01")
    assert first["sensor_type"] == "ultrasonic"
    assert "sensor_ts" in first


def test_pipeline_emits_sensor_and_fused_events_when_enabled(tmp_path):
    root = Path(__file__).resolve().parents[2]
    out_file = tmp_path / "events_sensor_modes.jsonl"
    legacy_graph = root / "configs" / "graphs" / "legacy_pipeline.yaml"

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["AI_MODEL_MODE"] = "mock"
    env["AI_SENSOR_ENABLED"] = "true"
    env["AI_SENSOR_TYPE"] = "ultrasonic"
    env["AI_SENSOR_ADAPTER"] = "ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource"
    env["AI_SENSOR_TIME_WINDOW_MS"] = "5000"
    env["AI_SENSOR_EMIT_EVENTS"] = "true"
    env["AI_SENSOR_EMIT_FUSED_EVENTS"] = "true"
    env["AI_FAKE_SENSOR_INTERVAL_SEC"] = "0.01"

    cmd = [
        sys.executable,
        "-m",
        "schnitzel_stream",
        "--graph",
        str(legacy_graph),
        "--output-jsonl",
        str(out_file),
        "--max-events",
        "14",
    ]
    result = subprocess.run(cmd, cwd=str(root), env=env, check=True)
    assert result.returncode == 0

    payloads = [
        json.loads(line)
        for line in out_file.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]
    assert any(p.get("event_type") == "SENSOR_EVENT" for p in payloads)
    assert any(p.get("event_type") == "FUSED_EVENT" for p in payloads)
