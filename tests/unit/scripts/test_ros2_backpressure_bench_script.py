from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


def _load_module(name: str, relative_path: str) -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / relative_path
    spec = importlib.util.spec_from_file_location(name, mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_apply_overflow_policy_variants():
    mod = _load_module(
        "run_ros2_backpressure_bench_policy_test_module",
        "scripts/experiments/run_ros2_backpressure_bench.py",
    )

    incoming = {"payload": {"group_id": "group_b"}, "meta": {"group_id": "group_b"}}
    base_queue = [
        {"payload": {"group_id": "group_a"}, "meta": {"group_id": "group_a"}},
        {"payload": {"group_id": "group_b"}, "meta": {"group_id": "group_b"}},
    ]

    q_drop_new = list(base_queue)
    accepted, dropped, err = mod._apply_overflow_policy(
        queue=q_drop_new,
        incoming=incoming,
        inbox_max=2,
        overflow_policy="drop_new",
        weight_key="group_id",
        default_weight=1.0,
        value_weights={"group_a": 1.0, "group_b": 2.0},
    )
    assert accepted is False
    assert dropped == 1
    assert err == ""
    assert q_drop_new == base_queue

    q_drop_oldest = list(base_queue)
    accepted, dropped, err = mod._apply_overflow_policy(
        queue=q_drop_oldest,
        incoming=incoming,
        inbox_max=2,
        overflow_policy="drop_oldest",
        weight_key="group_id",
        default_weight=1.0,
        value_weights={"group_a": 1.0, "group_b": 2.0},
    )
    assert accepted is True
    assert dropped == 1
    assert err == ""
    assert q_drop_oldest[0]["meta"]["group_id"] == "group_b"

    q_weighted = list(base_queue)
    accepted, dropped, err = mod._apply_overflow_policy(
        queue=q_weighted,
        incoming=incoming,
        inbox_max=2,
        overflow_policy="weighted_drop",
        weight_key="group_id",
        default_weight=1.0,
        value_weights={"group_a": 1.0, "group_b": 2.0},
    )
    assert accepted is True
    assert dropped == 1
    assert err == ""
    assert [row["meta"]["group_id"] for row in q_weighted] == ["group_b", "group_b"]

    q_error = list(base_queue)
    accepted, dropped, err = mod._apply_overflow_policy(
        queue=q_error,
        incoming=incoming,
        inbox_max=2,
        overflow_policy="error",
        weight_key="group_id",
        default_weight=1.0,
        value_weights={"group_a": 1.0, "group_b": 2.0},
    )
    assert accepted is False
    assert dropped == 0
    assert "policy=error" in err
    assert q_error == base_queue


def test_run_ros2_script_seed_and_run_id_with_stubbed_runner(tmp_path: Path, monkeypatch):
    mod = _load_module(
        "run_ros2_backpressure_bench_seed_test_module",
        "scripts/experiments/run_ros2_backpressure_bench.py",
    )

    monkeypatch.setattr(mod, "_import_ros2_modules", lambda: (object(), object(), object()))

    def _fake_run_ros2_once(*, graph, base_cfg, policy_cfg, workload_cfg, repeat, seed, session_dir, timeout_sec):
        policy_id = str(policy_cfg.get("policy_id", "unknown"))
        workload_id = str(workload_cfg.get("workload_id", "unknown"))
        run_id = f"run_{policy_id}_{workload_id}_r{int(repeat):02d}_s{int(seed)}"
        runs_dir = Path(session_dir) / "runs"
        events_dir = Path(session_dir) / "events"
        runs_dir.mkdir(parents=True, exist_ok=True)
        events_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "status": "ok",
            "error": "",
            "experiment_id": "backpressure_fairness",
            "policy_id": policy_id,
            "workload_id": workload_id,
            "seed": int(seed),
            "repeat": int(repeat),
            "run_id": run_id,
            "duration_sec": 1.0,
            "throughput": 100.0,
            "p50_latency_ms": 1.0,
            "p95_latency_ms": 2.0,
            "p99_latency_ms": 3.0,
            "drop_rate": 0.0,
            "event_miss_rate": 0.0,
            "recovery_time_ms": None,
            "group_id": "group_a",
            "group_miss_rate": 0.0,
            "group_latency_p95_ms": 2.0,
            "group_miss_gap": 0.0,
            "group_latency_gap_ms": 0.0,
            "harm_weighted_cost": 0.0,
            "metrics": {},
            "group_metrics": {},
            "runtime_metrics": {},
            "baseline_system": "ros2_transport",
            "paths": {
                "events_path": str(events_dir / f"{run_id}.jsonl"),
                "run_path": str(runs_dir / f"{run_id}.json"),
            },
        }
        Path(payload["paths"]["run_path"]).write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(mod, "_run_ros2_once", _fake_run_ros2_once)

    rc = mod.run(
        [
            "--base",
            "configs/experiments/backpressure_fairness/bench_base.yaml",
            "--policy",
            "configs/experiments/backpressure_fairness/policy_drop_new.yaml",
            "--workload",
            "configs/experiments/backpressure_fairness/workloads_balanced.yaml",
            "--repeats",
            "2",
            "--seed-base",
            "12000",
            "--out-dir",
            str(tmp_path / "ros2"),
            "--json",
        ]
    )
    assert rc == 0

    sessions = sorted((tmp_path / "ros2").glob("session_*"))
    assert sessions
    report = sessions[-1] / "session_report.json"
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["total_runs"] == 2
    run_rows = payload["runs"]
    assert [int(row["seed"]) for row in run_rows] == [12000, 1012000]
    assert run_rows[0]["run_id"] == "run_drop_new_balanced_r00_s12000"
    assert run_rows[1]["run_id"] == "run_drop_new_balanced_r01_s1012000"


def test_run_ros2_script_strict_fails_on_error(tmp_path: Path, monkeypatch):
    mod = _load_module(
        "run_ros2_backpressure_bench_strict_test_module",
        "scripts/experiments/run_ros2_backpressure_bench.py",
    )

    monkeypatch.setattr(mod, "_import_ros2_modules", lambda: (object(), object(), object()))

    def _fake_run_ros2_once(*, graph, base_cfg, policy_cfg, workload_cfg, repeat, seed, session_dir, timeout_sec):
        policy_id = str(policy_cfg.get("policy_id", "unknown"))
        workload_id = str(workload_cfg.get("workload_id", "unknown"))
        run_id = f"run_{policy_id}_{workload_id}_r{int(repeat):02d}_s{int(seed)}"
        return {
            "schema_version": 1,
            "status": "error",
            "error": "overflow",
            "experiment_id": "backpressure_fairness",
            "policy_id": policy_id,
            "workload_id": workload_id,
            "seed": int(seed),
            "repeat": int(repeat),
            "run_id": run_id,
            "duration_sec": 0.1,
            "throughput": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "drop_rate": 1.0,
            "event_miss_rate": 1.0,
            "recovery_time_ms": None,
            "group_id": "group_b",
            "group_miss_rate": 1.0,
            "group_latency_p95_ms": 0.0,
            "group_miss_gap": 1.0,
            "group_latency_gap_ms": 0.0,
            "harm_weighted_cost": 999.0,
            "metrics": {},
            "group_metrics": {},
            "runtime_metrics": {},
            "baseline_system": "ros2_transport",
            "paths": {},
        }

    monkeypatch.setattr(mod, "_run_ros2_once", _fake_run_ros2_once)

    rc = mod.run(
        [
            "--base",
            "configs/experiments/backpressure_fairness/bench_base.yaml",
            "--policy",
            "configs/experiments/backpressure_fairness/policy_error.yaml",
            "--workload",
            "configs/experiments/backpressure_fairness/workloads_balanced.yaml",
            "--repeats",
            "1",
            "--out-dir",
            str(tmp_path / "ros2"),
            "--strict",
        ]
    )
    assert rc == 1
