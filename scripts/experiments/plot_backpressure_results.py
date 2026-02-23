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

PLOT_METRICS = [
    ("harm_weighted_cost_mean", "Harm Weighted Cost (mean)"),
    ("event_miss_rate_mean", "Event Miss Rate (mean)"),
    ("p95_latency_ms_mean", "P95 Latency ms (mean)"),
    ("drop_rate_mean", "Drop Rate (mean)"),
]


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


def _build_svg(*, title: str, metric: str, rows: list[dict[str, Any]], out_path: Path) -> None:
    labels = [str(row.get("policy_id", "")) for row in rows]
    values: list[float] = []
    for row in rows:
        raw = row.get(metric)
        values.append(float(raw) if isinstance(raw, (int, float)) else 0.0)

    width = max(760, 180 + 120 * len(values))
    height = 420
    left = 80
    right = 24
    top = 70
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_val = max(values) if values else 1.0
    if max_val <= 0.0:
        max_val = 1.0

    n = max(1, len(values))
    slot_w = plot_w / n
    bar_w = min(72.0, slot_w * 0.65)
    x_axis_y = top + plot_h

    grid = []
    for i in range(6):
        y = top + plot_h - (plot_h * (i / 5.0))
        v = max_val * (i / 5.0)
        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_w:.2f}" y2="{y:.2f}" stroke="#d7dde5" stroke-width="1" />'
        )
        grid.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="11" fill="#344055">{v:.3g}</text>'
        )

    bars = []
    for idx, val in enumerate(values):
        cx = left + slot_w * idx + slot_w / 2.0
        bar_h = 0.0 if max_val <= 0 else (val / max_val) * plot_h
        x = cx - bar_w / 2.0
        y = x_axis_y - bar_h
        color = "#2a9d8f" if idx % 2 == 0 else "#457b9d"
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="{color}" rx="4" ry="4" />'
        )
        bars.append(
            f'<text x="{cx:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-size="11" fill="#1f2937">{val:.4g}</text>'
        )
        label = _svg_escape(labels[idx])
        bars.append(
            f'<text x="{cx:.2f}" y="{x_axis_y + 20:.2f}" text-anchor="middle" font-size="11" fill="#344055">{label}</text>'
        )

    svg = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect x="0" y="0" width="100%" height="100%" fill="#f7fafc" />',
            f'<text x="{left}" y="34" font-size="20" font-weight="700" fill="#1f2937">{_svg_escape(title)}</text>',
            f'<text x="{left}" y="54" font-size="12" fill="#4b5563">{_svg_escape(metric)}</text>',
            *grid,
            f'<line x1="{left}" y1="{x_axis_y:.2f}" x2="{left + plot_w:.2f}" y2="{x_axis_y:.2f}" stroke="#6b7280" stroke-width="1.5" />',
            *bars,
            '</svg>',
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
    for workload_id, items in sorted(by_workload.items()):
        ordered = sorted(items, key=lambda row: str(row.get("policy_id", "")))
        for metric, metric_title in PLOT_METRICS:
            svg_name = f"{_sanitize(workload_id)}__{_sanitize(metric)}.svg"
            svg_path = out_dir / svg_name
            _build_svg(
                title=f"{workload_id} - {metric_title}",
                metric=metric,
                rows=ordered,
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
    lines.append("")
    index_path.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "aggregate_json": str(aggregate_path),
        "plot_count": len(generated),
        "plots": generated,
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

