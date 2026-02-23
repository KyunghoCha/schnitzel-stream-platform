#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

SCHEMA_VERSION = 2
DEFAULT_AGGREGATE_JSON = "outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json"
DEFAULT_OUT_DIR = "outputs/experiments/backpressure_fairness/tables"


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _f(raw: Any, *, digits: int = 4) -> str:
    if isinstance(raw, (int, float)):
        return f"{float(raw):.{digits}f}"
    return "-"


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("workload_id", "")), str(row.get("policy_id", "")))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build markdown/csv tables for backpressure fairness paper draft")
    parser.add_argument("--aggregate-json", default=DEFAULT_AGGREGATE_JSON, help="aggregate json path")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="table output directory")
    parser.add_argument("--json", action="store_true", help="print machine-readable summary")
    parser.add_argument("--compact", action="store_true", help="compact JSON")
    return parser.parse_args(argv)


def _core_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Table 1. Core Performance and Reliability",
        "",
        "| Workload | Policy | N(ok) | Throughput | P95 Latency (ms) | Drop Rate | Miss Rate | Recovery (ms) | Harm Cost |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=_row_sort_key):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("workload_id", "")),
                    str(row.get("policy_id", "")),
                    str(row.get("ok_count", 0)),
                    _f(row.get("throughput_mean")),
                    _f(row.get("p95_latency_ms_mean")),
                    _f(row.get("drop_rate_mean")),
                    _f(row.get("event_miss_rate_mean")),
                    _f(row.get("recovery_time_ms_mean")),
                    _f(row.get("harm_weighted_cost_mean")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _fairness_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Table 2. Fairness-Sensitive Metrics",
        "",
        "| Workload | Policy | Worst Group | Worst Group Miss | Worst Group P95 (ms) | Group Miss Gap | Group Latency Gap (ms) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=_row_sort_key):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("workload_id", "")),
                    str(row.get("policy_id", "")),
                    str(row.get("worst_group_id_mode", "")),
                    _f(row.get("group_miss_rate_mean")),
                    _f(row.get("group_latency_p95_ms_mean")),
                    _f(row.get("group_miss_gap_mean")),
                    _f(row.get("group_latency_gap_ms_mean")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _ranking_table(ranking: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Table 3. Policy Ranking by Workload",
        "",
        "| Workload | Rank | Policy | Harm Cost | Miss Rate | P95 Latency (ms) |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in sorted(ranking, key=lambda r: (str(r.get("workload_id", "")), int(r.get("rank", 0)))):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("workload_id", "")),
                    str(row.get("rank", "")),
                    str(row.get("policy_id", "")),
                    _f(row.get("harm_weighted_cost_mean")),
                    _f(row.get("event_miss_rate_mean")),
                    _f(row.get("p95_latency_ms_mean")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _pairwise_table(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return [
            "## Table 4. Pairwise Significance and Effect Size",
            "",
            "No pairwise significance rows available.",
            "",
        ]

    lines = [
        "## Table 4. Pairwise Significance and Effect Size",
        "",
        "| Workload | Metric | Policy A | Policy B | Mean A | Mean B | Cliff's delta | p(MWU) | p(Holm) | Significant | Better |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    sorted_rows = sorted(
        rows,
        key=lambda r: (
            str(r.get("workload_id", "")),
            str(r.get("metric", "")),
            str(r.get("policy_a", "")),
            str(r.get("policy_b", "")),
        ),
    )
    for row in sorted_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("workload_id", "")),
                    str(row.get("metric", "")),
                    str(row.get("policy_a", "")),
                    str(row.get("policy_b", "")),
                    _f(row.get("mean_a")),
                    _f(row.get("mean_b")),
                    _f(row.get("effect_size_cliffs_delta")),
                    _f(row.get("p_value_mannwhitney")),
                    _f(row.get("p_value_holm")),
                    "yes" if bool(row.get("significant_0_05", False)) else "no",
                    str(row.get("better_policy", "")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _write_csv(path: Path, columns: list[str], source_rows: list[dict[str, Any]]) -> None:
    lines = [",".join(columns)]
    for row in source_rows:
        vals = []
        for col in columns:
            raw = row.get(col, "")
            if isinstance(raw, float):
                vals.append(f"{raw:.8f}")
            else:
                vals.append(str(raw))
        lines.append(",".join(vals))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    aggregate_path = _resolve_path(args.aggregate_json)
    if not aggregate_path.exists():
        print(f"Error: aggregate json not found: {aggregate_path}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(aggregate_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid aggregate json ({exc})", file=sys.stderr)
        return 2

    rows = payload.get("summary_rows")
    ranking = payload.get("ranking_by_workload")
    pairwise = payload.get("pairwise_tests", [])
    if not isinstance(rows, list) or not isinstance(ranking, list) or not isinstance(pairwise, list):
        print("Error: aggregate json missing summary rows/ranking/pairwise_tests", file=sys.stderr)
        return 2

    summary_rows = [r for r in rows if isinstance(r, dict)]
    ranking_rows = [r for r in ranking if isinstance(r, dict)]
    pairwise_rows = [r for r in pairwise if isinstance(r, dict)]

    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    markdown_lines = [
        "# Backpressure Fairness Study Tables",
        "",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Aggregate source: `{aggregate_path}`",
        "",
    ]
    markdown_lines.extend(_core_table(summary_rows))
    markdown_lines.extend(_fairness_table(summary_rows))
    markdown_lines.extend(_ranking_table(ranking_rows))
    markdown_lines.extend(_pairwise_table(pairwise_rows))

    markdown_path = out_dir / "research_tables.md"
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    core_csv_path = out_dir / "table_core_metrics.csv"
    fairness_csv_path = out_dir / "table_fairness_metrics.csv"
    ranking_csv_path = out_dir / "table_policy_ranking.csv"
    pairwise_csv_path = out_dir / "table_pairwise_significance.csv"

    _write_csv(
        core_csv_path,
        [
            "workload_id",
            "policy_id",
            "ok_count",
            "throughput_mean",
            "p95_latency_ms_mean",
            "drop_rate_mean",
            "event_miss_rate_mean",
            "recovery_time_ms_mean",
            "harm_weighted_cost_mean",
        ],
        summary_rows,
    )
    _write_csv(
        fairness_csv_path,
        [
            "workload_id",
            "policy_id",
            "worst_group_id_mode",
            "group_miss_rate_mean",
            "group_latency_p95_ms_mean",
            "group_miss_gap_mean",
            "group_latency_gap_ms_mean",
        ],
        summary_rows,
    )
    _write_csv(
        ranking_csv_path,
        [
            "workload_id",
            "rank",
            "policy_id",
            "harm_weighted_cost_mean",
            "event_miss_rate_mean",
            "p95_latency_ms_mean",
        ],
        ranking_rows,
    )
    _write_csv(
        pairwise_csv_path,
        [
            "workload_id",
            "metric",
            "policy_a",
            "policy_b",
            "n_a",
            "n_b",
            "mean_a",
            "mean_b",
            "delta_mean",
            "effect_size_cliffs_delta",
            "u_stat",
            "p_value_mannwhitney",
            "p_value_holm",
            "significant_0_05",
            "better_policy",
        ],
        pairwise_rows,
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "aggregate_json": str(aggregate_path),
        "markdown_path": str(markdown_path),
        "core_csv_path": str(core_csv_path),
        "fairness_csv_path": str(fairness_csv_path),
        "ranking_csv_path": str(ranking_csv_path),
        "pairwise_csv_path": str(pairwise_csv_path),
    }
    summary_path = out_dir / "tables_manifest.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"research_tables={markdown_path}")
        print(f"tables_manifest={summary_path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
