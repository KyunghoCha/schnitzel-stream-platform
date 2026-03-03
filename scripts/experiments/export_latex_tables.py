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

SCHEMA_VERSION = 1
DEFAULT_AGGREGATE_JSON = "outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json"
DEFAULT_ROS2_JSON = ""
DEFAULT_OUT_DIR = "docs/paper/backpressure_fairness/tables"


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _latex_escape(raw: Any) -> str:
    text = str(raw)
    repl = {
        "\\": r"\\textbackslash{}",
        "&": r"\\&",
        "%": r"\\%",
        "$": r"\\$",
        "#": r"\\#",
        "_": r"\\_",
        "{": r"\\{",
        "}": r"\\}",
        "~": r"\\textasciitilde{}",
        "^": r"\\textasciicircum{}",
    }
    out = text
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def _f(raw: Any, digits: int = 4) -> str:
    if isinstance(raw, (int, float)):
        return f"{float(raw):.{digits}f}"
    return "-"


def _table_file(path: Path, *, caption: str, label: str, headers: list[str], rows: list[list[str]]) -> None:
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{_latex_escape(caption)}}}",
        f"\\label{{{_latex_escape(label)}}}",
        f"\\begin{{tabular}}{{{'l' * len(headers)}}}",
        "\\hline",
        " & ".join(_latex_escape(h) for h in headers) + r" \\",
        "\\hline",
    ]
    for row in rows:
        lines.append(" & ".join(_latex_escape(x) for x in row) + r" \\")
    lines.extend(["\\hline", "\\end{tabular}", "\\end{table}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export aggregate experiment outputs into LaTeX table snippets")
    parser.add_argument("--aggregate-json", default=DEFAULT_AGGREGATE_JSON, help="aggregate json path")
    parser.add_argument("--ros2-json", default=DEFAULT_ROS2_JSON, help="optional ros2 comparison json path")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="latex table output directory")
    parser.add_argument("--json", action="store_true", help="print export manifest")
    parser.add_argument("--compact", action="store_true", help="compact JSON")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    aggregate_path = _resolve_path(args.aggregate_json)
    if not aggregate_path.exists():
        print(f"Error: aggregate json not found: {aggregate_path}", file=sys.stderr)
        return 2

    try:
        aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid aggregate json ({exc})", file=sys.stderr)
        return 2

    summary_rows_raw = aggregate.get("summary_rows")
    ranking_rows_raw = aggregate.get("ranking_by_workload")
    pairwise_rows_raw = aggregate.get("pairwise_tests")
    if not isinstance(summary_rows_raw, list) or not isinstance(ranking_rows_raw, list) or not isinstance(pairwise_rows_raw, list):
        print("Error: aggregate json missing summary_rows/ranking_by_workload/pairwise_tests", file=sys.stderr)
        return 2

    summary_rows = [r for r in summary_rows_raw if isinstance(r, dict)]
    ranking_rows = [r for r in ranking_rows_raw if isinstance(r, dict)]
    pairwise_rows = [r for r in pairwise_rows_raw if isinstance(r, dict)]

    ros2_payload: dict[str, Any] | None = None
    ros2_path_txt = str(args.ros2_json or "").strip()
    ros2_path = _resolve_path(ros2_path_txt) if ros2_path_txt else None
    if ros2_path is not None and ros2_path.exists():
        try:
            ros2_payload = json.loads(ros2_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Error: invalid ros2 json ({exc})", file=sys.stderr)
            return 2

    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    core_rows = []
    for row in sorted(summary_rows, key=lambda r: (str(r.get("workload_id", "")), str(r.get("policy_id", "")))):
        core_rows.append(
            [
                str(row.get("workload_id", "")),
                str(row.get("policy_id", "")),
                str(row.get("ok_count", "")),
                _f(row.get("throughput_mean")),
                _f(row.get("p95_latency_ms_mean")),
                _f(row.get("drop_rate_mean")),
                _f(row.get("event_miss_rate_mean")),
                _f(row.get("harm_weighted_cost_mean")),
            ]
        )
    core_path = out_dir / "table_core_metrics.tex"
    _table_file(
        core_path,
        caption="Core performance and reliability metrics.",
        label="tab:core_metrics",
        headers=["Workload", "Policy", "N", "Throughput", "P95 Latency", "Drop", "Miss", "Harm Cost"],
        rows=core_rows,
    )

    fairness_rows = []
    for row in sorted(summary_rows, key=lambda r: (str(r.get("workload_id", "")), str(r.get("policy_id", "")))):
        fairness_rows.append(
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
    fairness_path = out_dir / "table_fairness_metrics.tex"
    _table_file(
        fairness_path,
        caption="Fairness-sensitive metrics by policy and workload.",
        label="tab:fairness_metrics",
        headers=["Workload", "Policy", "Worst Group", "Worst Miss", "Worst P95", "Miss Gap", "Latency Gap"],
        rows=fairness_rows,
    )

    ranking_rows_out = []
    for row in sorted(ranking_rows, key=lambda r: (str(r.get("workload_id", "")), int(r.get("rank", 0)))):
        ranking_rows_out.append(
            [
                str(row.get("workload_id", "")),
                str(row.get("rank", "")),
                str(row.get("policy_id", "")),
                _f(row.get("harm_weighted_cost_mean")),
                _f(row.get("event_miss_rate_mean")),
                _f(row.get("p95_latency_ms_mean")),
            ]
        )
    ranking_path = out_dir / "table_policy_ranking.tex"
    _table_file(
        ranking_path,
        caption="Policy ranking by workload using fixed tie-breaking rule.",
        label="tab:policy_ranking",
        headers=["Workload", "Rank", "Policy", "Harm Cost", "Miss Rate", "P95 Latency"],
        rows=ranking_rows_out,
    )

    pairwise_sorted = sorted(
        pairwise_rows,
        key=lambda r: (
            str(r.get("workload_id", "")),
            str(r.get("metric", "")),
            1 if bool(r.get("significant_0_05", False)) else 2,
            float(r.get("p_value_holm")) if isinstance(r.get("p_value_holm"), (int, float)) else 9_999.0,
        ),
    )
    pairwise_rows_out = []
    for row in pairwise_sorted[:40]:
        pairwise_rows_out.append(
            [
                str(row.get("workload_id", "")),
                str(row.get("metric", "")),
                f"{row.get('policy_a', '')} vs {row.get('policy_b', '')}",
                _f(row.get("effect_size_cliffs_delta")),
                _f(row.get("p_value_mannwhitney")),
                _f(row.get("p_value_holm")),
                "yes" if bool(row.get("significant_0_05", False)) else "no",
                str(row.get("better_policy", "")),
            ]
        )
    pairwise_path = out_dir / "table_pairwise_significance.tex"
    _table_file(
        pairwise_path,
        caption="Pairwise policy significance and effect-size summary (top rows).",
        label="tab:pairwise_significance",
        headers=["Workload", "Metric", "Pair", "Cliff Delta", "p MWU", "p Holm", "Sig", "Better"],
        rows=pairwise_rows_out,
    )

    ros2_table_path = out_dir / "table_ros2_compare.tex"
    ros2_exported = False
    if isinstance(ros2_payload, dict):
        rows_raw = ros2_payload.get("comparisons")
        rows = [r for r in rows_raw if isinstance(r, dict)] if isinstance(rows_raw, list) else []
        ros2_rows = []
        for row in sorted(rows, key=lambda r: (str(r.get("workload_id", "")), str(r.get("policy_id", "")))):
            ros2_rows.append(
                [
                    str(row.get("workload_id", "")),
                    str(row.get("policy_id", "")),
                    _f(row.get("native_harm_weighted_cost_mean")),
                    _f(row.get("ros2_harm_weighted_cost_mean")),
                    _f(row.get("delta_harm_weighted_cost")),
                    str(row.get("winner_harm_weighted_cost", "")),
                    _f(row.get("native_p95_latency_ms_mean")),
                    _f(row.get("ros2_p95_latency_ms_mean")),
                ]
            )
        _table_file(
            ros2_table_path,
            caption="Native vs ROS2 appendix comparison.",
            label="tab:ros2_appendix_compare",
            headers=["Workload", "Policy", "Native Harm", "ROS2 Harm", "Delta Harm", "Winner", "Native P95", "ROS2 P95"],
            rows=ros2_rows,
        )
        ros2_exported = True
    else:
        _table_file(
            ros2_table_path,
            caption="Native vs ROS2 appendix comparison (not available in this run).",
            label="tab:ros2_appendix_compare",
            headers=["Workload", "Policy", "Native Harm", "ROS2 Harm", "Delta Harm", "Winner", "Native P95", "ROS2 P95"],
            rows=[["-", "-", "-", "-", "-", "-", "-", "-"]],
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "aggregate_json": str(aggregate_path),
        "ros2_json": str(ros2_path) if ros2_path is not None else "",
        "out_dir": str(out_dir),
        "tables": {
            "core": str(core_path),
            "fairness": str(fairness_path),
            "ranking": str(ranking_path),
            "pairwise": str(pairwise_path),
            "ros2": str(ros2_table_path) if ros2_exported else "",
        },
        "ros2_exported": ros2_exported,
    }
    manifest_path = out_dir / "latex_tables_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"latex_tables_manifest={manifest_path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
