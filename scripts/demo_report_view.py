#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/professor_showcase_guide.md
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import sys
from typing import Any


def _resolve_path(raw: str, *, base: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (base / p).resolve()


def _load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("report top-level must be a JSON object")
    return obj


def _scenario_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = payload.get("scenarios", [])
    if not isinstance(scenarios, list):
        return []
    out: list[dict[str, Any]] = []
    for item in scenarios:
        if isinstance(item, dict):
            out.append(item)
    return out


def _step_tail(scenario: dict[str, Any]) -> str:
    steps = scenario.get("steps", [])
    if not isinstance(steps, list) or not steps:
        return ""
    last = steps[-1]
    if not isinstance(last, dict):
        return ""
    stderr_tail = str(last.get("stderr_tail", "") or "").strip()
    stdout_tail = str(last.get("stdout_tail", "") or "").strip()
    tail = stderr_tail if stderr_tail else stdout_tail
    if not tail:
        return ""
    lines = tail.splitlines()
    return lines[-1].strip()


def _render_markdown(payload: dict[str, Any], *, source_path: Path) -> str:
    rows = _scenario_rows(payload)
    lines = [
        "# Demo Report Summary",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- source_report: `{source_path}`",
        f"- schema_version: `{payload.get('schema_version', 'n/a')}`",
        f"- profile: `{payload.get('profile', 'n/a')}`",
        f"- status: `{payload.get('status', 'n/a')}`",
        f"- exit_code: `{payload.get('exit_code', 'n/a')}`",
        "",
        "| Scenario | Title | Status | Failure Kind | Failure Reason | Tail |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {sid} | {title} | {status} | {kind} | {reason} | {tail} |".format(
                sid=str(row.get("id", "")),
                title=str(row.get("title", "")).replace("|", "/"),
                status=str(row.get("status", "")),
                kind=str(row.get("failure_kind", "")),
                reason=str(row.get("failure_reason", "")),
                tail=_step_tail(row).replace("|", "/"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _render_html(payload: dict[str, Any], *, source_path: Path) -> str:
    rows = _scenario_rows(payload)
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('id', '')))}</td>"
            f"<td>{html.escape(str(row.get('title', '')))}</td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td>{html.escape(str(row.get('failure_kind', '')))}</td>"
            f"<td>{html.escape(str(row.get('failure_reason', '')))}</td>"
            f"<td>{html.escape(_step_tail(row))}</td>"
            "</tr>"
        )
    body_rows = "\n".join(table_rows)
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <title>Demo Report Summary</title>\n"
        "  <style>\n"
        "    body { font-family: Arial, sans-serif; margin: 24px; }\n"
        "    table { border-collapse: collapse; width: 100%; }\n"
        "    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }\n"
        "    th { background: #f5f5f5; }\n"
        "    code { background: #f7f7f7; padding: 2px 4px; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <h1>Demo Report Summary</h1>\n"
        "  <ul>\n"
        f"    <li>generated_at: {html.escape(datetime.now(timezone.utc).isoformat())}</li>\n"
        f"    <li>source_report: <code>{html.escape(str(source_path))}</code></li>\n"
        f"    <li>schema_version: <code>{html.escape(str(payload.get('schema_version', 'n/a')))}</code></li>\n"
        f"    <li>profile: <code>{html.escape(str(payload.get('profile', 'n/a')))}</code></li>\n"
        f"    <li>status: <code>{html.escape(str(payload.get('status', 'n/a')))}</code></li>\n"
        f"    <li>exit_code: <code>{html.escape(str(payload.get('exit_code', 'n/a')))}</code></li>\n"
        "  </ul>\n"
        "  <table>\n"
        "    <thead>\n"
        "      <tr><th>Scenario</th><th>Title</th><th>Status</th><th>Failure Kind</th><th>Failure Reason</th><th>Tail</th></tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        f"{body_rows}\n"
        "    </tbody>\n"
        "  </table>\n"
        "</body>\n"
        "</html>\n"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render demo_pack JSON report as Markdown/HTML summary")
    parser.add_argument("--report", required=True, help="Path to demo_pack JSON report")
    parser.add_argument("--format", choices=("md", "html", "both"), default="both", help="Output format")
    parser.add_argument("--out-dir", default="", help="Output directory (default: report directory)")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cwd = Path.cwd()
    report_path = _resolve_path(str(args.report), base=cwd)
    if not report_path.exists():
        print(f"Error: report not found: {report_path}", file=sys.stderr)
        return 1

    try:
        payload = _load_payload(report_path)
    except Exception as exc:
        print(f"Error: failed to load report: {exc}", file=sys.stderr)
        return 1

    out_dir = _resolve_path(str(args.out_dir), base=cwd) if args.out_dir else report_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = report_path.stem
    outputs: list[Path] = []

    if args.format in {"md", "both"}:
        md_path = out_dir / f"{stem}.summary.md"
        md_path.write_text(_render_markdown(payload, source_path=report_path), encoding="utf-8")
        outputs.append(md_path)

    if args.format in {"html", "both"}:
        html_path = out_dir / f"{stem}.summary.html"
        html_path.write_text(_render_html(payload, source_path=report_path), encoding="utf-8")
        outputs.append(html_path)

    for path in outputs:
        print(f"generated={path}")
    # Intent: report rendering is a post-processing utility; missing optional fields should not fail rendering.
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
