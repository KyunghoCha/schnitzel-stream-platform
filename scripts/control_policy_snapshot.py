#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
from typing import Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

POLICY_ENV_KEYS = [
    "SS_CONTROL_API_TOKEN",
    "SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS",
    "SS_AUDIT_MAX_BYTES",
    "SS_AUDIT_MAX_FILES",
    "SS_CONTROL_API_CORS_ORIGINS",
]

DEFAULT_BASELINE = "configs/policy/control_api_policy_snapshot_v1.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit/check control API policy snapshot")
    parser.add_argument("--check", action="store_true", help="Compare emitted snapshot with baseline")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Baseline JSON path")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON output")
    return parser.parse_args(argv)


@contextmanager
def _clean_policy_env() -> Iterator[None]:
    original = {key: os.environ.get(key) for key in POLICY_ENV_KEYS}
    try:
        for key in POLICY_ENV_KEYS:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def build_snapshot() -> dict[str, object]:
    from schnitzel_stream.control_api import app as app_mod
    from schnitzel_stream.control_api import audit as audit_mod
    from schnitzel_stream.control_api import auth as auth_mod

    with _clean_policy_env():
        return {
            "schema_version": 1,
            "security": {
                "security_mode_no_token": str(auth_mod.security_mode()),
                "mutation_auth_mode_no_token": str(auth_mod.mutation_auth_mode()),
                "local_mutation_override_enabled_no_token": bool(auth_mod.local_mutation_override_enabled()),
                "env_token": str(auth_mod.ENV_CONTROL_API_TOKEN),
                "env_local_mutation_override": str(auth_mod.ENV_ALLOW_LOCAL_MUTATIONS),
            },
            "audit": {
                "default_path": "outputs/audit/stream_control_audit.jsonl",
                "default_max_bytes": int(audit_mod.audit_max_bytes_from_env()),
                "default_max_files": int(audit_mod.audit_max_files_from_env()),
                "env_max_bytes": str(audit_mod.ENV_AUDIT_MAX_BYTES),
                "env_max_files": str(audit_mod.ENV_AUDIT_MAX_FILES),
            },
            "cors": {
                "default_origins": list(app_mod._cors_origins_from_env()),
                "env_cors_origins": "SS_CONTROL_API_CORS_ORIGINS",
            },
            "mutating_endpoints": [
                "POST /api/v1/presets/{preset_id}/run",
                "POST /api/v1/fleet/start",
                "POST /api/v1/fleet/stop",
            ],
        }


def _render_json(payload: dict[str, object], *, compact: bool) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_snapshot()

    if args.check:
        baseline = Path(str(args.baseline))
        if not baseline.is_absolute():
            baseline = (PROJECT_ROOT / baseline).resolve()
        if not baseline.exists():
            print(f"Error: baseline not found: {baseline}", file=sys.stderr)
            return 2
        try:
            expected = json.loads(baseline.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Error: invalid baseline JSON ({exc})", file=sys.stderr)
            return 2
        if payload != expected:
            print("Error: control policy snapshot drift detected", file=sys.stderr)
            print(f"baseline={baseline}", file=sys.stderr)
            print(_render_json(payload, compact=bool(args.compact)), file=sys.stderr)
            return 1

    print(_render_json(payload, compact=bool(args.compact)))
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
