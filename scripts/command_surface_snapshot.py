#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/lab_rc_release_checklist.md
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from typing import Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

DEFAULT_BASELINE = "configs/policy/command_surface_snapshot_v1.json"
EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2


@contextmanager
def _stable_import_path() -> Iterator[None]:
    original = list(sys.path)
    try:
        src = str((PROJECT_ROOT / "src").resolve())
        if src not in sys.path:
            sys.path.insert(0, src)
        yield
    finally:
        sys.path[:] = original


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit/check frozen command surface snapshot (Lab RC)")
    parser.add_argument("--check", action="store_true", help="Compare emitted snapshot with baseline")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Baseline JSON path")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON output")
    return parser.parse_args(argv)


def build_snapshot() -> dict[str, object]:
    with _stable_import_path():
        from schnitzel_stream import __version__

    return {
        "schema_version": 1,
        "release_target": "lab_rc",
        "freeze_scope": "core_ops",
        "version": str(__version__),
        "commands": [
            {
                "id": "core.cli.run",
                "entrypoint": "python -m schnitzel_stream",
                "kind": "core",
                "frozen": True,
            },
            {
                "id": "core.cli.validate",
                "entrypoint": "python -m schnitzel_stream validate",
                "kind": "core",
                "frozen": True,
            },
            {
                "id": "ops.stream_run",
                "entrypoint": "python scripts/stream_run.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.stream_fleet",
                "entrypoint": "python scripts/stream_fleet.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.stream_monitor",
                "entrypoint": "python scripts/stream_monitor.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.stream_console",
                "entrypoint": "python scripts/stream_console.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.env_doctor",
                "entrypoint": "python scripts/env_doctor.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.graph_wizard",
                "entrypoint": "python scripts/graph_wizard.py",
                "kind": "ops",
                "frozen": True,
            },
            {
                "id": "ops.stream_control_api",
                "entrypoint": "python scripts/stream_control_api.py",
                "kind": "ops",
                "frozen": True,
            },
        ],
        "non_frozen_surfaces": [
            "experimental preset options (--experimental)",
            "experimental yolo presets and model stack",
            "advanced block editor interaction/ui polish tracks",
        ],
    }


def _render_json(payload: dict[str, object], *, compact: bool) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _resolve_baseline(path_value: str) -> Path:
    baseline = Path(str(path_value).strip())
    if baseline.is_absolute():
        return baseline
    return (PROJECT_ROOT / baseline).resolve()


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    snapshot = build_snapshot()
    status = "ok"
    drift: list[str] = []

    if bool(args.check):
        baseline = _resolve_baseline(str(args.baseline))
        if not baseline.exists():
            print(f"Error: baseline not found: {baseline}", file=sys.stderr)
            return EXIT_USAGE
        try:
            expected = json.loads(baseline.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Error: invalid baseline JSON ({exc})", file=sys.stderr)
            return EXIT_USAGE
        if snapshot != expected:
            status = "drift"
            drift.append("command surface snapshot does not match baseline")

    report = {
        "schema_version": int(snapshot.get("schema_version", 1)),
        "status": status,
        "commands": snapshot.get("commands", []),
        "drift": drift,
    }

    if bool(args.check):
        if status == "drift":
            print("Error: command surface drift detected", file=sys.stderr)
            print(_render_json(report, compact=bool(args.compact)), file=sys.stderr)
            return EXIT_DRIFT
        print(_render_json(report, compact=bool(args.compact)))
        return EXIT_OK

    print(_render_json(snapshot, compact=bool(args.compact)))
    return EXIT_OK


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
