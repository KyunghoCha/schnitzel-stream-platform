#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import glob
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

SCHEMA_VERSION = 1
DEFAULT_NATIVE_RUNS_GLOB = "outputs/experiments/backpressure_fairness/session_*/runs/run_*.json"
DEFAULT_ROS2_RUNS_GLOB = "outputs/experiments/backpressure_fairness/ros2_baseline/session_*/runs/run_*.json"
DEFAULT_OUT_DIR = "outputs/experiments/backpressure_fairness/ros2_baseline/compare"

SUMMARY_METRICS = [
    "throughput",
    "p95_latency_ms",
    "drop_rate",
    "event_miss_rate",
    "harm_weighted_cost",
    "group_miss_gap",
    "group_latency_gap_ms",
]

LOWER_IS_BETTER = {
    "p95_latency_ms",
    "drop_rate",
    "event_miss_rate",
    "harm_weighted_cost",
    "group_miss_gap",
    "group_latency_gap_ms",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _glob_paths(pattern: str) -> list[Path]:
    raw = str(pattern or "").strip()
    if not raw:
        return []
    p = Path(raw)
    if p.is_absolute():
        return sorted(Path(x).resolve() for x in glob.glob(raw, recursive=True))
    root = _resolve_path(".")
    full_pattern = str(root / raw)
    return sorted(Path(x).resolve() for x in glob.glob(full_pattern, recursive=True))


def _load_runs(paths: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload["_path"] = str(path)
            out.append(payload)
    return out


def _as_float(raw: Any) -> float | None:
    if not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if not math.isfinite(value):
        return None
    return value


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    return float(statistics.stdev(values))


def _collect_metric(rows: list[dict[str, Any]], metric: str) -> list[float]:
    vals = [_as_float(r.get(metric)) for r in rows]
    return [float(v) for v in vals if v is not None]


def _summarize_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in runs:
        policy_id = str(row.get("policy_id", "")).strip()
        workload_id = str(row.get("workload_id", "")).strip()
        if not policy_id or not workload_id:
            continue
        groups.setdefault((policy_id, workload_id), []).append(row)

    out: list[dict[str, Any]] = []
    for (policy_id, workload_id), items in sorted(groups.items()):
        ok_rows = [r for r in items if str(r.get("status", "")) == "ok"]
        row: dict[str, Any] = {
            "policy_id": policy_id,
            "workload_id": workload_id,
            "run_count": len(items),
            "ok_count": len(ok_rows),
            "error_count": len(items) - len(ok_rows),
        }
        for metric in SUMMARY_METRICS:
            values = _collect_metric(ok_rows, metric)
            row[f"{metric}_mean"] = _mean(values)
            row[f"{metric}_std"] = _std(values)
        out.append(row)
    return out


def _compare_rows(native_rows: list[dict[str, Any]], ros2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    native_index = {(str(r.get("policy_id", "")), str(r.get("workload_id", ""))): r for r in native_rows}
    ros2_index = {(str(r.get("policy_id", "")), str(r.get("workload_id", ""))): r for r in ros2_rows}
    keys = sorted(set(native_index.keys()) & set(ros2_index.keys()))

    out: list[dict[str, Any]] = []
    for key in keys:
        policy_id, workload_id = key
        n = native_index[key]
        r = ros2_index[key]

        row: dict[str, Any] = {
            "policy_id": policy_id,
            "workload_id": workload_id,
        }
        for metric in SUMMARY_METRICS:
            n_mean = _as_float(n.get(f"{metric}_mean"))
            r_mean = _as_float(r.get(f"{metric}_mean"))
            delta = None
            winner = ""
            if n_mean is not None and r_mean is not None:
                delta = float(n_mean - r_mean)
                if metric in LOWER_IS_BETTER:
                    winner = "native" if n_mean < r_mean else "ros2"
                else:
                    winner = "native" if n_mean > r_mean else "ros2"
            row[f"native_{metric}_mean"] = n_mean
            row[f"ros2_{metric}_mean"] = r_mean
            row[f"delta_{metric}"] = delta
            row[f"winner_{metric}"] = winner
        out.append(row)
    return out


def _reproducibility_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    ok_rows = [r for r in runs if str(r.get("status", "")) == "ok"]
    failed = total - len(ok_rows)
    failure_rate = float(failed / total) if total > 0 else 0.0

    cvs: list[float] = []
    for metric in SUMMARY_METRICS:
        values = _collect_metric(ok_rows, metric)
        mean_v = _mean(values)
        std_v = _std(values)
        if mean_v is None or std_v is None:
            continue
        denom = abs(float(mean_v))
        if denom <= 1e-12:
            continue
        cvs.append(float(std_v / denom))

    cv_mean = _mean(cvs) if cvs else None
    cv_max = max(cvs) if cvs else None
    replay_stability = None if cv_mean is None else float(1.0 / (1.0 + cv_mean))

    return {
        "runs_total": int(total),
        "runs_ok": int(len(ok_rows)),
        "runs_failed": int(failed),
        "failure_rate": float(failure_rate),
        "repro_cv_mean": cv_mean,
        "repro_cv_max": cv_max,
        "replay_stability_score": replay_stability,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare native benchmark runs against ROS2 baseline runs")
    parser.add_argument("--native-runs-glob", default=DEFAULT_NATIVE_RUNS_GLOB, help="glob for native run json files")
    parser.add_argument("--ros2-runs-glob", default=DEFAULT_ROS2_RUNS_GLOB, help="glob for ROS2 run json files")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="output directory")
    parser.add_argument("--compact", action="store_true", help="compact JSON stdout")
    parser.add_argument("--json", action="store_true", help="print comparison json")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    native_paths = _glob_paths(args.native_runs_glob)
    ros2_paths = _glob_paths(args.ros2_runs_glob)
    if not native_paths:
        print(f"Error: no native run files found for pattern: {args.native_runs_glob}", file=sys.stderr)
        return 2
    if not ros2_paths:
        print(f"Error: no ROS2 run files found for pattern: {args.ros2_runs_glob}", file=sys.stderr)
        return 2

    native_runs = _load_runs(native_paths)
    ros2_runs = _load_runs(ros2_paths)
    if not native_runs:
        print("Error: no valid native run payloads found", file=sys.stderr)
        return 2
    if not ros2_runs:
        print("Error: no valid ROS2 run payloads found", file=sys.stderr)
        return 2

    native_summary = _summarize_runs(native_runs)
    ros2_summary = _summarize_runs(ros2_runs)
    comparisons = _compare_rows(native_summary, ros2_summary)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "native_runs_glob": str(args.native_runs_glob),
        "ros2_runs_glob": str(args.ros2_runs_glob),
        "native_runs_total": len(native_runs),
        "ros2_runs_total": len(ros2_runs),
        "native_summary_rows": native_summary,
        "ros2_summary_rows": ros2_summary,
        "comparisons": comparisons,
        "reproducibility": {
            "native": _reproducibility_summary(native_runs),
            "ros2": _reproducibility_summary(ros2_runs),
        },
        "metric_keys": SUMMARY_METRICS,
    }

    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "ros2_comparison.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    comp_csv = out_dir / "ros2_comparison.csv"
    comp_fields = sorted({k for row in comparisons for k in row.keys()}) if comparisons else ["policy_id", "workload_id"]
    with comp_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=comp_fields)
        writer.writeheader()
        for row in comparisons:
            writer.writerow(row)

    repro_csv = out_dir / "ros2_reproducibility.csv"
    repro_rows = [
        {"system": "native", **payload["reproducibility"]["native"]},
        {"system": "ros2", **payload["reproducibility"]["ros2"]},
    ]
    repro_fields = [
        "system",
        "runs_total",
        "runs_ok",
        "runs_failed",
        "failure_rate",
        "repro_cv_mean",
        "repro_cv_max",
        "replay_stability_score",
    ]
    with repro_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=repro_fields)
        writer.writeheader()
        for row in repro_rows:
            writer.writerow(row)

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"native_runs={len(native_runs)} ros2_runs={len(ros2_runs)}")
        print(f"comparison_json={json_path}")
        print(f"comparison_csv={comp_csv}")
        print(f"repro_csv={repro_csv}")

    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
