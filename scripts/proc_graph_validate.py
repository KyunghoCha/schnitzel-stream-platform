#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/process_graph_foundation_guide.md
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

EXIT_OK = 0
EXIT_GENERAL_ERROR = 1
EXIT_VALIDATION_ERROR = 2


def _resolve_spec_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate process-graph specification (foundation mode)")
    parser.add_argument("--spec", required=True, help="Path to process graph spec (version: 1)")
    parser.add_argument("--report-json", action="store_true", help="Print validation report as JSON")
    return parser.parse_args(argv)


def _load_validator_api() -> tuple[type[Exception], object]:
    from schnitzel_stream.procgraph.validate import ProcessGraphValidationError, validate_process_graph

    return ProcessGraphValidationError, validate_process_graph


def _ok_payload(report: object) -> dict[str, object]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "engine": "procgraph.foundation",
        "spec": getattr(report, "spec_path"),
        "process_count": int(getattr(report, "process_count")),
        "channel_count": int(getattr(report, "channel_count")),
        "link_count": int(getattr(report, "link_count")),
        "resolved_process_graphs": dict(getattr(report, "resolved_process_graphs")),
        "resolved_channel_paths": dict(getattr(report, "resolved_channel_paths")),
    }


def _error_payload(*, kind: str, spec: Path, message: str) -> dict[str, object]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "engine": "procgraph.foundation",
        "error_kind": kind,
        "spec": str(spec),
        "message": str(message),
    }


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    spec_path = _resolve_spec_path(str(args.spec))

    try:
        validation_error_type, validate_fn = _load_validator_api()
    except Exception as exc:
        # Intent: dependency/import failures should return a stable general error code.
        if args.report_json:
            print(json.dumps(_error_payload(kind="runtime", spec=spec_path, message=str(exc)), separators=(",", ":")))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return EXIT_GENERAL_ERROR

    try:
        report = validate_fn(spec_path)
    except validation_error_type as exc:  # type: ignore[misc]
        if args.report_json:
            print(json.dumps(_error_payload(kind="validation", spec=spec_path, message=str(exc)), separators=(",", ":")))
        else:
            print(f"Validation failed: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except Exception as exc:
        # Intent: keep script failure contract explicit for automation.
        if args.report_json:
            print(json.dumps(_error_payload(kind="runtime", spec=spec_path, message=str(exc)), separators=(",", ":")))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return EXIT_GENERAL_ERROR

    if args.report_json:
        print(json.dumps(_ok_payload(report), separators=(",", ":")))
    else:
        print("process graph validation ok")
        print(f"spec={report.spec_path}")
        print(
            f"processes={report.process_count} channels={report.channel_count} links={report.link_count}",
        )
        for process_id, graph_path in sorted(report.resolved_process_graphs.items()):
            print(f"process[{process_id}]={graph_path}")
        for channel_id, channel_path in sorted(report.resolved_channel_paths.items()):
            print(f"channel[{channel_id}]={channel_path}")

    return EXIT_OK


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
