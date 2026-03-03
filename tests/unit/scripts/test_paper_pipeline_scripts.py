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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_export_latex_tables_script(tmp_path: Path):
    export_mod = _load_module(
        "export_latex_tables_test_module",
        "scripts/experiments/export_latex_tables.py",
    )

    aggregate_json = tmp_path / "agg.json"
    _write_json(
        aggregate_json,
        {
            "summary_rows": [
                {
                    "workload_id": "balanced",
                    "policy_id": "drop_new",
                    "ok_count": 3,
                    "throughput_mean": 100.0,
                    "p95_latency_ms_mean": 12.0,
                    "drop_rate_mean": 0.03,
                    "event_miss_rate_mean": 0.04,
                    "harm_weighted_cost_mean": 15.0,
                    "worst_group_id_mode": "group_b",
                    "group_miss_rate_mean": 0.06,
                    "group_latency_p95_ms_mean": 13.5,
                    "group_miss_gap_mean": 0.02,
                    "group_latency_gap_ms_mean": 1.2,
                }
            ],
            "ranking_by_workload": [
                {
                    "workload_id": "balanced",
                    "rank": 1,
                    "policy_id": "drop_new",
                    "harm_weighted_cost_mean": 15.0,
                    "event_miss_rate_mean": 0.04,
                    "p95_latency_ms_mean": 12.0,
                }
            ],
            "pairwise_tests": [
                {
                    "workload_id": "balanced",
                    "metric": "harm_weighted_cost",
                    "policy_a": "drop_new",
                    "policy_b": "drop_oldest",
                    "effect_size_cliffs_delta": -0.22,
                    "p_value_mannwhitney": 0.03,
                    "p_value_holm": 0.04,
                    "significant_0_05": True,
                    "better_policy": "drop_new",
                }
            ],
        },
    )

    ros2_json = tmp_path / "ros2.json"
    _write_json(
        ros2_json,
        {
            "comparisons": [
                {
                    "workload_id": "balanced",
                    "policy_id": "drop_new",
                    "native_harm_weighted_cost_mean": 15.0,
                    "ros2_harm_weighted_cost_mean": 18.0,
                    "delta_harm_weighted_cost": -3.0,
                    "winner_harm_weighted_cost": "native",
                    "native_p95_latency_ms_mean": 12.0,
                    "ros2_p95_latency_ms_mean": 14.0,
                }
            ]
        },
    )

    out_dir = tmp_path / "latex"
    rc = export_mod.run(
        [
            "--aggregate-json",
            str(aggregate_json),
            "--ros2-json",
            str(ros2_json),
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0

    manifest_path = out_dir / "latex_tables_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert bool(manifest.get("ros2_exported", False)) is True
    assert (out_dir / "table_core_metrics.tex").exists()
    assert (out_dir / "table_fairness_metrics.tex").exists()
    assert (out_dir / "table_policy_ranking.tex").exists()
    assert (out_dir / "table_pairwise_significance.tex").exists()
    assert (out_dir / "table_ros2_compare.tex").exists()


def test_run_paper_pipeline_script_smoke(tmp_path: Path):
    pipeline_mod = _load_module(
        "run_paper_pipeline_test_module",
        "scripts/experiments/run_paper_pipeline.py",
    )

    analysis_yaml = tmp_path / "analysis.yaml"
    analysis_yaml.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "quality_gates:",
                "  schema_requirements:",
                "    aggregate:",
                "      - summary_rows",
                "      - pairwise_tests",
                "      - ranking_by_workload",
                "      - significance_alpha",
                "      - pairwise_metric_keys",
                "    ros2_compare:",
                "      - native_summary_rows",
                "      - ros2_summary_rows",
                "      - comparisons",
                "      - reproducibility",
                "",
            ]
        ),
        encoding="utf-8",
    )

    matrix_yaml = tmp_path / "matrix.yaml"
    matrix_yaml.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "matrix_id: smoke",
                "experiment_id: backpressure_fairness",
                "base_config: configs/experiments/backpressure_fairness/bench_base.yaml",
                f"analysis_spec: {analysis_yaml}",
                "policies:",
                "  - configs/experiments/backpressure_fairness/policy_drop_new.yaml",
                "workloads:",
                "  - configs/experiments/backpressure_fairness/workloads_balanced.yaml",
                "execution:",
                "  repeats: 1",
                "  seed_base: 12000",
                "  max_runs: 1",
                "  strict: false",
                "  quality_profile: none",
                "  continue_on_ros2_missing: true",
                "paths:",
                f"  output_root: {tmp_path / 'out'}",
                "  ros2_runs_glob: outputs/experiments/backpressure_fairness/ros2_baseline/session_*/runs/run_*.json",
                "",
            ]
        ),
        encoding="utf-8",
    )

    rc = pipeline_mod.run(
        [
            "--matrix",
            str(matrix_yaml),
            "--analysis-spec",
            str(analysis_yaml),
            "--out-root",
            str(tmp_path / "out"),
            "--quality-profile",
            "none",
            "--max-runs",
            "1",
            "--skip-ros2-compare",
        ]
    )
    assert rc == 0

    pkg_dir = tmp_path / "out" / "package"
    manifest_path = pkg_dir / "artifacts_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["quality"]["profile"] == "none"
    assert payload["contracts"]["missing_aggregate_keys"] == []

    assert (pkg_dir / "repro_commands.md").exists()
    assert (pkg_dir / "submission_checklist.md").exists()
    assert Path(payload["artifacts"]["aggregate_json"]).exists()
    assert Path(payload["artifacts"]["research_tables"]).exists()
    assert Path(payload["artifacts"]["latex_manifest"]).exists()
