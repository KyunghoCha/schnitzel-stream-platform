#!/usr/bin/env python3
# scripts/graph_wizard.py
# Docs: docs/ops/command_reference.md, docs/guides/graph_wizard_guide.md
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Add project src path for direct script execution.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.ops import graph_wizard as wizard_ops


EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_PRECONDITION = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Template-driven graph authoring wizard (non-interactive)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list-profiles", action="store_true", help="List available template profiles")
    mode.add_argument("--profile", default="", help="Profile id to generate graph from")
    mode.add_argument("--validate", action="store_true", help="Validate an existing graph spec file")

    parser.add_argument("--out", default="", help="Output graph path for --profile mode")
    parser.add_argument("--spec", default="", help="Graph spec path for --validate mode")
    parser.add_argument("--experimental", action="store_true", help="Allow experimental profiles")
    parser.add_argument("--max-events", type=int, default=None, help="Optional event budget mapped to source max_frames")
    parser.add_argument("--input-path", default="", help="Override file input path")
    parser.add_argument("--camera-index", type=int, default=None, help="Override webcam index")
    parser.add_argument("--device", default="", help="YOLO device override (for example: cpu, 0)")
    parser.add_argument("--model-path", default="", help="YOLO model path override")
    parser.add_argument("--loop", choices=("true", "false"), default="", help="Override file loop behavior")
    parser.add_argument("--validate-after-generate", action="store_true", help="Validate graph after generation")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    return parser.parse_args(argv)


def _print_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _repo_root() -> Path:
    return PROJECT_ROOT


def _list_profiles(*, table: dict[str, wizard_ops.GraphWizardProfile], include_experimental: bool, as_json: bool) -> int:
    rows = wizard_ops.list_profile_rows(table=table, include_experimental=include_experimental)
    if as_json:
        _print_json(
            {
                "schema_version": 1,
                "mode": "list_profiles",
                "experimental_included": bool(include_experimental),
                "profiles": [
                    {
                        "profile_id": row[0],
                        "experimental": row[1] == "yes",
                        "template": row[2],
                        "description": row[3],
                    }
                    for row in rows
                ],
                "count": len(rows),
            }
        )
        return EXIT_OK

    print("profile_id\texperimental\ttemplate\tdescription")
    for row in rows:
        print("\t".join(row))
    if not include_experimental:
        print("hint: add --experimental to include opt-in profiles")
    return EXIT_OK


def run(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else EXIT_USAGE
        return code if code != 0 else EXIT_OK

    repo_root = _repo_root()
    try:
        table = wizard_ops.load_profile_table(repo_root)

        if bool(args.list_profiles):
            return _list_profiles(table=table, include_experimental=bool(args.experimental), as_json=bool(args.json))

        if bool(args.validate):
            result = wizard_ops.validate_graph_file(repo_root=repo_root, spec_path=str(args.spec))
            payload = {
                "schema_version": 1,
                "mode": "validate",
                "spec": str(result.spec_path),
                "ok": bool(result.ok),
                "error": result.error,
            }
            if bool(args.json):
                _print_json(payload)
            else:
                print(
                    "validate "
                    f"spec={result.spec_path} "
                    f"status={'ok' if result.ok else 'failed'}"
                )
                if result.error:
                    print(f"error={result.error}")
            if result.ok:
                return EXIT_OK
            # Intent: graph validation failures are precondition failures for execution pipelines.
            return EXIT_PRECONDITION

        generated = wizard_ops.generate_graph(
            repo_root=repo_root,
            table=table,
            profile_id=str(args.profile),
            out_path=str(args.out),
            allow_experimental=bool(args.experimental),
            input_path=str(args.input_path),
            camera_index=int(args.camera_index) if args.camera_index is not None else None,
            device=str(args.device),
            model_path=str(args.model_path),
            loop=str(args.loop),
            max_events=int(args.max_events) if args.max_events is not None else None,
        )
        validation = None
        if bool(args.validate_after_generate):
            validation = wizard_ops.validate_graph_file(repo_root=repo_root, spec_path=str(generated.output_path))
            if not validation.ok:
                if bool(args.json):
                    _print_json(
                        {
                            "schema_version": 1,
                            "mode": "generate",
                            "profile_id": generated.profile_id,
                            "output_path": str(generated.output_path),
                            "validation": {
                                "ok": False,
                                "error": validation.error,
                            },
                        }
                    )
                else:
                    print(
                        "generated "
                        f"profile={generated.profile_id} "
                        f"out={generated.output_path} "
                        "validation=failed"
                    )
                    print(f"error={validation.error}")
                return EXIT_PRECONDITION

        if bool(args.json):
            _print_json(
                {
                    "schema_version": 1,
                    "mode": "generate",
                    "profile_id": generated.profile_id,
                    "output_path": str(generated.output_path),
                    "template_path": str(generated.template_path),
                    "experimental": generated.experimental,
                    "overrides": dict(generated.overrides),
                    "max_events": generated.max_events,
                    "validation": {
                        "enabled": bool(args.validate_after_generate),
                        "ok": True if validation is None else bool(validation.ok),
                    },
                }
            )
        else:
            print(
                "generated "
                f"profile={generated.profile_id} "
                f"out={generated.output_path} "
                f"validation={'ok' if bool(args.validate_after_generate) else 'skipped'}"
            )
        return EXIT_OK
    except wizard_ops.GraphWizardUsageError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except wizard_ops.GraphWizardPreconditionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_PRECONDITION
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_FAILED


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
