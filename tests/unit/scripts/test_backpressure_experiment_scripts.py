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


def _write_run(
    path: Path,
    *,
    policy: str,
    workload: str,
    seed: int,
    harm: float,
    miss: float,
    p95: float,
    throughput: float = 100.0,
    status: str = "ok",
) -> None:
    payload = {
        "schema_version": 1,
        "status": status,
        "policy_id": policy,
        "workload_id": workload,
        "seed": seed,
        "repeat": 0,
        "run_id": f"run_{policy}_{workload}_{seed}",
        "duration_sec": 1.2,
        "throughput": throughput,
        "p50_latency_ms": 2.0,
        "p95_latency_ms": p95,
        "p99_latency_ms": p95 * 1.2,
        "drop_rate": miss * 0.8,
        "event_miss_rate": miss,
        "recovery_time_ms": p95 * 0.7,
        "group_id": "group_b",
        "group_miss_rate": miss * 1.1,
        "group_latency_p95_ms": p95 * 1.05,
        "harm_weighted_cost": harm,
        "group_miss_gap": miss * 0.2,
        "group_latency_gap_ms": p95 * 0.1,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_experiment_aggregate_plot_table_scripts(tmp_path: Path):
    aggregate_mod = _load_module(
        "aggregate_backpressure_results_test_module",
        "scripts/experiments/aggregate_backpressure_results.py",
    )
    plot_mod = _load_module(
        "plot_backpressure_results_test_module",
        "scripts/experiments/plot_backpressure_results.py",
    )
    table_mod = _load_module(
        "build_research_tables_test_module",
        "scripts/experiments/build_research_tables.py",
    )

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    _write_run(runs_dir / "run_a_bal_1.json", policy="drop_new", workload="balanced", seed=1, harm=18.0, miss=0.05, p95=12.0)
    _write_run(runs_dir / "run_a_bal_2.json", policy="drop_new", workload="balanced", seed=2, harm=20.0, miss=0.07, p95=13.0)
    _write_run(
        runs_dir / "run_b_bal_1.json",
        policy="drop_oldest",
        workload="balanced",
        seed=3,
        harm=15.0,
        miss=0.03,
        p95=10.0,
    )
    _write_run(
        runs_dir / "run_b_bal_2.json",
        policy="drop_oldest",
        workload="balanced",
        seed=4,
        harm=16.0,
        miss=0.02,
        p95=11.0,
    )

    aggregate_out = tmp_path / "aggregate"
    rc = aggregate_mod.run(["--runs-glob", str(runs_dir / "run_*.json"), "--out-dir", str(aggregate_out)])
    assert rc == 0

    aggregate_json = aggregate_out / "backpressure_aggregate.json"
    assert aggregate_json.exists()
    payload = json.loads(aggregate_json.read_text(encoding="utf-8"))
    assert int(payload["schema_version"]) >= 1
    assert payload["group_count"] == 2
    assert isinstance(payload.get("pairwise_tests"), list)
    assert len(payload["pairwise_tests"]) >= 1
    assert (aggregate_out / "backpressure_pairwise_tests.csv").exists()

    plot_out = tmp_path / "plots"
    rc = plot_mod.run(["--aggregate-json", str(aggregate_json), "--out-dir", str(plot_out)])
    assert rc == 0
    manifest = plot_out / "plots_manifest.json"
    assert manifest.exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert int(manifest_payload["plot_count"]) >= 1

    tables_out = tmp_path / "tables"
    rc = table_mod.run(["--aggregate-json", str(aggregate_json), "--out-dir", str(tables_out)])
    assert rc == 0
    assert (tables_out / "research_tables.md").exists()
    assert (tables_out / "tables_manifest.json").exists()
    assert (tables_out / "table_pairwise_significance.csv").exists()


def test_compare_ros2_baseline_script(tmp_path: Path):
    compare_mod = _load_module(
        "compare_ros2_baseline_test_module",
        "scripts/experiments/compare_ros2_baseline.py",
    )

    native_runs = tmp_path / "native_runs"
    ros2_runs = tmp_path / "ros2_runs"
    native_runs.mkdir(parents=True, exist_ok=True)
    ros2_runs.mkdir(parents=True, exist_ok=True)

    _write_run(native_runs / "run_n1.json", policy="drop_new", workload="balanced", seed=11, harm=13.0, miss=0.03, p95=10.0, throughput=125.0)
    _write_run(native_runs / "run_n2.json", policy="drop_new", workload="balanced", seed=12, harm=14.0, miss=0.04, p95=11.0, throughput=121.0)

    _write_run(ros2_runs / "run_r1.json", policy="drop_new", workload="balanced", seed=21, harm=17.0, miss=0.06, p95=13.0, throughput=112.0)
    _write_run(ros2_runs / "run_r2.json", policy="drop_new", workload="balanced", seed=22, harm=18.0, miss=0.07, p95=14.0, throughput=110.0)

    out_dir = tmp_path / "compare"
    rc = compare_mod.run(
        [
            "--native-runs-glob",
            str(native_runs / "run_*.json"),
            "--ros2-runs-glob",
            str(ros2_runs / "run_*.json"),
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0

    comparison_json = out_dir / "ros2_comparison.json"
    assert comparison_json.exists()
    payload = json.loads(comparison_json.read_text(encoding="utf-8"))
    assert payload["native_runs_total"] == 2
    assert payload["ros2_runs_total"] == 2
    assert len(payload["comparisons"]) == 1
    comp = payload["comparisons"][0]
    assert comp["winner_harm_weighted_cost"] == "native"
    assert comp["winner_throughput"] == "native"
    assert isinstance(payload["reproducibility"].get("native", {}), dict)
    assert isinstance(payload["reproducibility"].get("ros2", {}), dict)
