#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]

SCHEMA_VERSION = 1
DEFAULT_AGGREGATE_JSON = "outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json"
DEFAULT_OUT_DIR = "outputs/experiments/backpressure_fairness/plots"

PLOT_METRICS: list[dict[str, str]] = [
    {
        "metric": "harm_weighted_cost_mean",
        "title": "Harm Weighted Cost (mean, 95% CI)",
        "ci_low": "harm_weighted_cost_ci95_low",
        "ci_high": "harm_weighted_cost_ci95_high",
    },
    {
        "metric": "p95_latency_ms_mean",
        "title": "P95 Latency ms (mean, 95% CI)",
        "ci_low": "p95_latency_ms_ci95_low",
        "ci_high": "p95_latency_ms_ci95_high",
    },
    {
        "metric": "throughput_mean",
        "title": "Throughput (mean, 95% CI)",
        "ci_low": "throughput_ci95_low",
        "ci_high": "throughput_ci95_high",
    },
    {
        "metric": "recovery_time_ms_mean",
        "title": "Recovery Time ms (mean, 95% CI)",
        "ci_low": "recovery_time_ms_ci95_low",
        "ci_high": "recovery_time_ms_ci95_high",
    },
    {
        "metric": "group_latency_gap_ms_mean",
        "title": "Group Latency Gap ms (mean, 95% CI)",
        "ci_low": "group_latency_gap_ms_ci95_low",
        "ci_high": "group_latency_gap_ms_ci95_high",
    },
]

POLICY_ORDER = ["drop_new", "drop_oldest", "weighted_drop", "error"]


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _sanitize(raw: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in str(raw))
    return out.strip("_") or "x"


def _svg_escape(raw: str) -> str:
    return (
        str(raw)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _to_float(raw: Any) -> float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        val = float(raw)
        return val if math.isfinite(val) else None
    return None


def _policy_sort_key(policy_id: str) -> tuple[int, str]:
    if policy_id in POLICY_ORDER:
        return (POLICY_ORDER.index(policy_id), policy_id)
    return (len(POLICY_ORDER) + 1, policy_id)


def _collect_points(rows: list[dict[str, Any]], metric_cfg: dict[str, str]) -> list[dict[str, Any]]:
    metric = metric_cfg["metric"]
    ci_low = metric_cfg["ci_low"]
    ci_high = metric_cfg["ci_high"]
    points: list[dict[str, Any]] = []
    for row in rows:
        policy_id = str(row.get("policy_id", "")).strip() or "unknown"
        mean_v = _to_float(row.get(metric))
        lo_v = _to_float(row.get(ci_low))
        hi_v = _to_float(row.get(ci_high))
        if mean_v is None:
            lo_v = None
            hi_v = None
        else:
            lo_v = lo_v if lo_v is not None else mean_v
            hi_v = hi_v if hi_v is not None else mean_v
            if lo_v > hi_v:
                lo_v, hi_v = hi_v, lo_v
        points.append(
            {
                "policy_id": policy_id,
                "mean": mean_v,
                "ci_low": lo_v,
                "ci_high": hi_v,
            }
        )
    points.sort(key=lambda item: _policy_sort_key(str(item["policy_id"])))
    return points


def _metric_has_variation(points: list[dict[str, Any]]) -> tuple[bool, str]:
    vals = [float(item["mean"]) for item in points if item.get("mean") is not None]
    if len(vals) < 2:
        return False, "insufficient_non_null_values"
    span = max(vals) - min(vals)
    if math.isclose(span, 0.0, rel_tol=1e-9, abs_tol=1e-12):
        return False, "policy_invariant_metric"
    return True, ""


def _tick_label(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if abs(value) >= 1:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _build_svg(
    *,
    title: str,
    metric: str,
    points: list[dict[str, Any]],
    out_path: Path,
) -> None:
    width = max(760, 180 + 130 * len(points))
    height = 430
    left = 88
    right = 24
    top = 78
    bottom = 95
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_axis_y = top + plot_h

    y_candidates: list[float] = []
    for p in points:
        mean_v = p.get("mean")
        if mean_v is None:
            continue
        y_candidates.append(float(mean_v))
        lo = p.get("ci_low")
        hi = p.get("ci_high")
        if lo is not None:
            y_candidates.append(float(lo))
        if hi is not None:
            y_candidates.append(float(hi))
    if not y_candidates:
        y_min = 0.0
        y_max = 1.0
    else:
        y_min = min(y_candidates)
        y_max = max(y_candidates)
        spread = y_max - y_min
        if spread <= 0.0:
            pad = max(1.0, abs(y_max) * 0.1)
        else:
            pad = spread * 0.12
        y_min -= pad
        y_max += pad
        if math.isclose(y_min, y_max):
            y_max = y_min + 1.0

    def y_of(v: float) -> float:
        return top + (y_max - v) / (y_max - y_min) * plot_h

    grid: list[str] = []
    for i in range(6):
        frac = i / 5.0
        y = top + plot_h - plot_h * frac
        v = y_min + (y_max - y_min) * frac
        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w:.2f}" y2="{y:.2f}" stroke="#d7dde5" stroke-width="1" />'
        )
        grid.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#344055">{_svg_escape(_tick_label(v))}</text>'
        )

    n = max(1, len(points))
    slot_w = plot_w / n
    marks: list[str] = []
    for idx, p in enumerate(points):
        cx = left + slot_w * idx + slot_w / 2.0
        label = _svg_escape(str(p["policy_id"]))
        mean_v = p.get("mean")
        if mean_v is None:
            # Explicit NA marker for failed/empty policy results.
            y = x_axis_y - 18.0
            marks.append(f'<line x1="{cx - 6:.2f}" y1="{y - 6:.2f}" x2="{cx + 6:.2f}" y2="{y + 6:.2f}" stroke="#b91c1c" stroke-width="2" />')
            marks.append(f'<line x1="{cx - 6:.2f}" y1="{y + 6:.2f}" x2="{cx + 6:.2f}" y2="{y - 6:.2f}" stroke="#b91c1c" stroke-width="2" />')
            marks.append(
                f'<text x="{cx:.2f}" y="{y - 10:.2f}" text-anchor="middle" font-size="11" fill="#b91c1c">NA</text>'
            )
        else:
            color = "#1d4ed8" if idx % 2 == 0 else "#0f766e"
            mean_f = float(mean_v)
            lo = float(p.get("ci_low") if p.get("ci_low") is not None else mean_f)
            hi = float(p.get("ci_high") if p.get("ci_high") is not None else mean_f)
            y_mean = y_of(mean_f)
            y_lo = y_of(lo)
            y_hi = y_of(hi)
            marks.append(f'<line x1="{cx:.2f}" y1="{y_lo:.2f}" x2="{cx:.2f}" y2="{y_hi:.2f}" stroke="{color}" stroke-width="2.2" />')
            marks.append(f'<line x1="{cx - 7:.2f}" y1="{y_lo:.2f}" x2="{cx + 7:.2f}" y2="{y_lo:.2f}" stroke="{color}" stroke-width="2" />')
            marks.append(f'<line x1="{cx - 7:.2f}" y1="{y_hi:.2f}" x2="{cx + 7:.2f}" y2="{y_hi:.2f}" stroke="{color}" stroke-width="2" />')
            marks.append(f'<circle cx="{cx:.2f}" cy="{y_mean:.2f}" r="4.6" fill="{color}" />')
            marks.append(
                f'<text x="{cx:.2f}" y="{y_mean - 10:.2f}" text-anchor="middle" font-size="11" fill="#1f2937">{_svg_escape(_tick_label(mean_f))}</text>'
            )
        marks.append(
            f'<text x="{cx:.2f}" y="{x_axis_y + 24:.2f}" text-anchor="middle" font-size="11" fill="#344055">{label}</text>'
        )

    svg = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect x="0" y="0" width="100%" height="100%" fill="#f7fafc" />',
            f'<text x="{left}" y="34" font-size="20" font-weight="700" fill="#1f2937">{_svg_escape(title)}</text>',
            f'<text x="{left}" y="54" font-size="12" fill="#4b5563">{_svg_escape(metric)}</text>',
            f'<text x="{width - 26}" y="34" text-anchor="end" font-size="11" fill="#4b5563">points = mean, whiskers = 95% CI, NA = failed/no metric</text>',
            *grid,
            f'<line x1="{left}" y1="{x_axis_y:.2f}" x2="{left + plot_w:.2f}" y2="{x_axis_y:.2f}" stroke="#6b7280" stroke-width="1.5" />',
            *marks,
            "</svg>",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render simple SVG plots from aggregate benchmark JSON")
    parser.add_argument("--aggregate-json", default=DEFAULT_AGGREGATE_JSON, help="aggregate json path")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="plot output directory")
    parser.add_argument("--json", action="store_true", help="print machine-readable manifest")
    parser.add_argument("--compact", action="store_true", help="compact JSON output")
    return parser.parse_args(argv)


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
    if not isinstance(rows, list):
        print("Error: aggregate json missing summary_rows", file=sys.stderr)
        return 2

    by_workload: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        workload_id = str(row.get("workload_id", "")).strip()
        if not workload_id:
            continue
        by_workload.setdefault(workload_id, []).append(row)

    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for workload_id, items in sorted(by_workload.items()):
        ordered = sorted(items, key=lambda row: _policy_sort_key(str(row.get("policy_id", ""))))
        for metric_cfg in PLOT_METRICS:
            metric = metric_cfg["metric"]
            metric_title = metric_cfg["title"]
            points = _collect_points(ordered, metric_cfg)
            ok, reason = _metric_has_variation(points)
            if not ok:
                skipped.append(
                    {
                        "workload_id": workload_id,
                        "metric": metric,
                        "reason": reason,
                    }
                )
                continue
            svg_name = f"{_sanitize(workload_id)}__{_sanitize(metric)}.svg"
            svg_path = out_dir / svg_name
            _build_svg(
                title=f"{workload_id} - {metric_title}",
                metric=metric,
                points=points,
                out_path=svg_path,
            )
            generated.append(
                {
                    "workload_id": workload_id,
                    "metric": metric,
                    "title": metric_title,
                    "path": str(svg_path),
                }
            )

    index_path = out_dir / "plots_index.md"
    lines = [
        "# Backpressure Fairness Plots",
        "",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Source aggregate: `{aggregate_path}`",
        "",
    ]
    current_workload = ""
    for item in generated:
        workload = item["workload_id"]
        if workload != current_workload:
            current_workload = workload
            lines.append(f"## {workload}")
            lines.append("")
        p = Path(item["path"])
        lines.append(f"- {item['title']}: `{p.name}`")
    if skipped:
        lines.extend(["", "## Skipped Metrics", ""])
        for item in skipped:
            lines.append(
                f"- {item['workload_id']} / {item['metric']}: {item['reason']}"
            )
    lines.append("")
    index_path.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "aggregate_json": str(aggregate_path),
        "plot_count": len(generated),
        "skipped_count": len(skipped),
        "plots": generated,
        "skipped": skipped,
        "index_markdown": str(index_path),
    }
    manifest_path = out_dir / "plots_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"plot_count={manifest['plot_count']}")
        print(f"plots_manifest={manifest_path}")
        print(f"plots_index={index_path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
