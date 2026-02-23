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

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]


SCHEMA_VERSION = 2
DEFAULT_RUNS_GLOB = "outputs/experiments/backpressure_fairness/session_*/runs/run_*.json"
DEFAULT_OUT_DIR = "outputs/experiments/backpressure_fairness/aggregate"

METRIC_KEYS = [
    "throughput",
    "p50_latency_ms",
    "p95_latency_ms",
    "p99_latency_ms",
    "drop_rate",
    "event_miss_rate",
    "recovery_time_ms",
    "harm_weighted_cost",
    "group_miss_gap",
    "group_latency_gap_ms",
    "group_miss_rate",
    "group_latency_p95_ms",
]

PAIRWISE_METRIC_KEYS = [
    "harm_weighted_cost",
    "event_miss_rate",
    "p95_latency_ms",
    "group_miss_gap",
    "group_latency_gap_ms",
    "drop_rate",
]

# Lower is better for all metrics used in pairwise policy comparison.
LOWER_IS_BETTER_METRICS = set(PAIRWISE_METRIC_KEYS)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _as_float(raw: Any) -> float | None:
    if not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if not math.isfinite(value):
        return None
    return value


def _bootstrap_ci(values: list[float], *, seed: int = 1337, samples: int = 2000) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    if len(values) == 1:
        return float(values[0]), float(values[0])
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(samples, len(arr)))
    means = arr[idx].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _stdev(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    return float(statistics.stdev(values))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def _mode_str(values: list[str]) -> str:
    if not values:
        return ""
    counts: dict[str, int] = {}
    for item in values:
        key = str(item)
        counts[key] = int(counts.get(key, 0)) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


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


def _aggregate_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in METRIC_KEYS:
        vals = [_as_float(row.get(key)) for row in rows]
        clean = [float(v) for v in vals if v is not None]
        mean_v = _mean(clean)
        std_v = _stdev(clean)
        med_v = _median(clean)
        ci_low, ci_high = _bootstrap_ci(clean)
        summary[f"{key}_mean"] = mean_v
        summary[f"{key}_std"] = std_v
        summary[f"{key}_median"] = med_v
        summary[f"{key}_min"] = min(clean) if clean else None
        summary[f"{key}_max"] = max(clean) if clean else None
        summary[f"{key}_ci95_low"] = ci_low
        summary[f"{key}_ci95_high"] = ci_high
    return summary


def _ranking_by_workload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_workload: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_workload.setdefault(str(row["workload_id"]), []).append(row)
    out: list[dict[str, Any]] = []
    for workload_id, items in sorted(by_workload.items()):
        ranked = sorted(
            items,
            key=lambda r: (
                float(r.get("harm_weighted_cost_mean") or 1_000_000.0),
                float(r.get("event_miss_rate_mean") or 1_000_000.0),
                float(r.get("p95_latency_ms_mean") or 1_000_000.0),
                str(r.get("policy_id", "")),
            ),
        )
        for rank, item in enumerate(ranked, start=1):
            out.append(
                {
                    "workload_id": workload_id,
                    "rank": int(rank),
                    "policy_id": str(item.get("policy_id", "")),
                    "harm_weighted_cost_mean": item.get("harm_weighted_cost_mean"),
                    "event_miss_rate_mean": item.get("event_miss_rate_mean"),
                    "p95_latency_ms_mean": item.get("p95_latency_ms_mean"),
                }
            )
    return out


def _metric_series(rows: list[dict[str, Any]], metric: str) -> list[float]:
    vals = [_as_float(row.get(metric)) for row in rows]
    return [float(v) for v in vals if v is not None]


def _cliffs_delta(xs: list[float], ys: list[float]) -> float | None:
    if not xs or not ys:
        return None
    gt = 0
    lt = 0
    for x in xs:
        for y in ys:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    total = len(xs) * len(ys)
    if total <= 0:
        return None
    return float((gt - lt) / total)


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda kv: kv[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def _mann_whitney_u_p_value(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    if len(xs) < 2 or len(ys) < 2:
        return None, None

    n1 = len(xs)
    n2 = len(ys)
    combined = xs + ys
    ranks = _average_ranks(combined)
    r1 = sum(ranks[:n1])
    u1 = r1 - (n1 * (n1 + 1) / 2.0)
    u2 = n1 * n2 - u1
    u = min(u1, u2)

    tie_counts: dict[float, int] = {}
    for value in combined:
        tie_counts[value] = int(tie_counts.get(value, 0)) + 1
    tie_term = sum((count**3 - count) for count in tie_counts.values() if count > 1)

    mean_u = n1 * n2 / 2.0
    denom = (n1 + n2) * (n1 + n2 - 1)
    correction = (tie_term / denom) if denom > 0 else 0.0
    var_u = (n1 * n2 / 12.0) * ((n1 + n2 + 1) - correction)
    if var_u <= 0.0:
        return float(u), None

    z = (u - mean_u + 0.5 * (1.0 if u < mean_u else -1.0)) / math.sqrt(var_u)
    p_two_sided = max(0.0, min(1.0, 2.0 * (1.0 - _normal_cdf(abs(z)))))
    return float(u), float(p_two_sided)


def _holm_adjust(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    m = len(p_values)
    order = sorted(range(m), key=lambda idx: p_values[idx])
    adjusted_sorted = [0.0] * m
    running_max = 0.0
    for rank, original_idx in enumerate(order, start=1):
        scale = m - rank + 1
        candidate = min(1.0, float(p_values[original_idx]) * scale)
        running_max = max(running_max, candidate)
        adjusted_sorted[rank - 1] = running_max

    adjusted = [1.0] * m
    for rank, original_idx in enumerate(order, start=1):
        adjusted[original_idx] = adjusted_sorted[rank - 1]
    return adjusted


def _pairwise_tests(runs: list[dict[str, Any]], *, alpha: float) -> list[dict[str, Any]]:
    by_workload_policy: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in runs:
        if str(row.get("status", "")) != "ok":
            continue
        workload_id = str(row.get("workload_id", "")).strip()
        policy_id = str(row.get("policy_id", "")).strip()
        if not workload_id or not policy_id:
            continue
        by_workload_policy.setdefault((workload_id, policy_id), []).append(row)

    by_workload: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for (workload_id, policy_id), items in by_workload_policy.items():
        by_workload.setdefault(workload_id, {})[policy_id] = items

    all_tests: list[dict[str, Any]] = []
    for workload_id, policies in sorted(by_workload.items()):
        policy_ids = sorted(policies.keys())
        for metric in PAIRWISE_METRIC_KEYS:
            tests_for_metric: list[dict[str, Any]] = []
            for idx in range(len(policy_ids)):
                for jdx in range(idx + 1, len(policy_ids)):
                    pa = policy_ids[idx]
                    pb = policy_ids[jdx]
                    xa = _metric_series(policies[pa], metric)
                    xb = _metric_series(policies[pb], metric)
                    mean_a = _mean(xa)
                    mean_b = _mean(xb)
                    delta_mean = (float(mean_a) - float(mean_b)) if mean_a is not None and mean_b is not None else None
                    cliffs = _cliffs_delta(xa, xb)
                    u_stat, p_value = _mann_whitney_u_p_value(xa, xb)

                    better = ""
                    lower_better = metric in LOWER_IS_BETTER_METRICS
                    if mean_a is not None and mean_b is not None:
                        if lower_better:
                            better = pa if float(mean_a) < float(mean_b) else pb
                        else:
                            better = pa if float(mean_a) > float(mean_b) else pb

                    tests_for_metric.append(
                        {
                            "workload_id": workload_id,
                            "metric": metric,
                            "policy_a": pa,
                            "policy_b": pb,
                            "n_a": len(xa),
                            "n_b": len(xb),
                            "mean_a": mean_a,
                            "mean_b": mean_b,
                            "delta_mean": delta_mean,
                            "effect_size_cliffs_delta": cliffs,
                            "u_stat": u_stat,
                            "p_value_mannwhitney": p_value,
                            "lower_is_better": lower_better,
                            "better_policy": better,
                        }
                    )

            pvals = [float(t["p_value_mannwhitney"]) for t in tests_for_metric if isinstance(t.get("p_value_mannwhitney"), float)]
            adjusted = _holm_adjust(pvals)
            p_iter = iter(adjusted)
            for row in tests_for_metric:
                if isinstance(row.get("p_value_mannwhitney"), float):
                    p_holm = next(p_iter)
                    row["p_value_holm"] = p_holm
                    row["significant_0_05"] = bool(p_holm <= float(alpha))
                else:
                    row["p_value_holm"] = None
                    row["significant_0_05"] = False

            all_tests.extend(tests_for_metric)

    return all_tests


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate backpressure benchmark run JSON files")
    parser.add_argument("--runs-glob", default=DEFAULT_RUNS_GLOB, help="glob for run json files")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="output directory")
    parser.add_argument("--alpha", type=float, default=0.05, help="significance threshold for Holm-adjusted p-values")
    parser.add_argument("--compact", action="store_true", help="compact JSON stdout")
    parser.add_argument("--json", action="store_true", help="print aggregate json")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_paths = _glob_paths(args.runs_glob)
    if not run_paths:
        print(f"Error: no run files found for pattern: {args.runs_glob}", file=sys.stderr)
        return 2

    runs = _load_runs(run_paths)
    if not runs:
        print("Error: no valid run payloads found", file=sys.stderr)
        return 2

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in runs:
        key = (str(row.get("policy_id", "")), str(row.get("workload_id", "")))
        groups.setdefault(key, []).append(row)

    summary_rows: list[dict[str, Any]] = []
    for (policy_id, workload_id), items in sorted(groups.items()):
        ok_rows = [row for row in items if str(row.get("status", "")) == "ok"]
        err_rows = [row for row in items if str(row.get("status", "")) != "ok"]
        agg = _aggregate_group(ok_rows)
        summary_row = {
            "policy_id": policy_id,
            "workload_id": workload_id,
            "run_count": len(items),
            "ok_count": len(ok_rows),
            "error_count": len(err_rows),
            "worst_group_id_mode": _mode_str([str(row.get("group_id", "")) for row in ok_rows]),
        }
        summary_row.update(agg)
        summary_rows.append(summary_row)

    pairwise_tests = _pairwise_tests(runs, alpha=float(args.alpha))
    ranking = _ranking_by_workload(summary_rows)
    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    aggregate_payload = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "runs_glob": str(args.runs_glob),
        "runs_total": len(runs),
        "group_count": len(summary_rows),
        "summary_rows": summary_rows,
        "pairwise_tests": pairwise_tests,
        "ranking_by_workload": ranking,
        "metric_keys": METRIC_KEYS,
        "pairwise_metric_keys": PAIRWISE_METRIC_KEYS,
        "significance_alpha": float(args.alpha),
    }

    aggregate_json_path = out_dir / "backpressure_aggregate.json"
    aggregate_json_path.write_text(json.dumps(aggregate_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = out_dir / "backpressure_summary.csv"
    csv_fields = sorted({key for row in summary_rows for key in row.keys()})
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    pairwise_csv_path = out_dir / "backpressure_pairwise_tests.csv"
    pairwise_fields = sorted({key for row in pairwise_tests for key in row.keys()}) if pairwise_tests else []
    with pairwise_csv_path.open("w", encoding="utf-8", newline="") as f:
        if pairwise_fields:
            writer = csv.DictWriter(f, fieldnames=pairwise_fields)
            writer.writeheader()
            for row in pairwise_tests:
                writer.writerow(row)

    ranking_csv_path = out_dir / "backpressure_ranking.csv"
    ranking_fields = ["workload_id", "rank", "policy_id", "harm_weighted_cost_mean", "event_miss_rate_mean", "p95_latency_ms_mean"]
    with ranking_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ranking_fields)
        writer.writeheader()
        for row in ranking:
            writer.writerow(row)

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(aggregate_payload, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(aggregate_payload, ensure_ascii=False, indent=2))
    else:
        print(f"runs_total={aggregate_payload['runs_total']} group_count={aggregate_payload['group_count']}")
        print(f"aggregate_json={aggregate_json_path}")
        print(f"summary_csv={csv_path}")
        print(f"pairwise_csv={pairwise_csv_path}")
        print(f"ranking_csv={ranking_csv_path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
