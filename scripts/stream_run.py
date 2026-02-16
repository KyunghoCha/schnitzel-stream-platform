#!/usr/bin/env python3
# scripts/stream_run.py
# Docs: docs/ops/command_reference.md
"""
One-command preset launcher for common v2 stream workflows.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Add project src path for direct script execution.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.ops import presets as preset_ops


EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_USAGE = 2


def _repo_root() -> Path:
    return preset_ops.repo_root_from_script(Path(__file__))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-command v2 stream preset launcher")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List available presets")
    mode.add_argument("--preset", default="", help="Preset id to run")

    parser.add_argument("--experimental", action="store_true", help="Allow experimental presets")
    parser.add_argument("--validate-only", action="store_true", help="Validate graph and exit")
    parser.add_argument("--max-events", type=int, default=None, help="Max source packet budget")
    parser.add_argument("--input-path", default="", help="Override file input path for file-based presets")
    parser.add_argument("--camera-index", type=int, default=None, help="Override camera index for webcam presets")
    parser.add_argument("--device", default="", help="YOLO device override (for example: cpu, 0)")
    parser.add_argument(
        "--loop",
        choices=("true", "false"),
        default="",
        help="Override file loop behavior for file-based presets",
    )
    return parser.parse_args(argv)


def _list_presets(*, table: dict[str, preset_ops.PresetSpec], include_experimental: bool) -> int:
    rows = preset_ops.list_presets_rows(table=table, include_experimental=include_experimental)
    print("preset_id\texperimental\tgraph\tdescription")
    for row in rows:
        print("\t".join(row))
    if not include_experimental:
        print("hint: add --experimental to list opt-in presets")
    return EXIT_OK


def _build_env(*, repo_root: Path, spec: preset_ops.PresetSpec, args: argparse.Namespace) -> dict[str, str]:
    return preset_ops.build_preset_env(
        repo_root=repo_root,
        spec=spec,
        input_path=str(args.input_path),
        camera_index=int(args.camera_index) if args.camera_index is not None else None,
        device=str(args.device),
        loop=str(args.loop),
    )


def _shell_cmd(cmd: list[str]) -> str:
    return preset_ops.shell_cmd(cmd)


def _run_subprocess(*, cmd: list[str], cwd: Path, env: dict[str, str]) -> int:
    return preset_ops.run_subprocess(cmd=cmd, cwd=cwd, env=env)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()
    table = preset_ops.build_preset_table(repo_root)

    if bool(args.list):
        return _list_presets(table=table, include_experimental=bool(args.experimental))

    preset_id = str(args.preset or "").strip()
    if not preset_id:
        print("Error: --preset is required unless --list is used", file=sys.stderr)
        return EXIT_USAGE

    spec = table.get(preset_id)
    if spec is None:
        print(f"Error: unknown preset: {preset_id}", file=sys.stderr)
        return EXIT_USAGE
    if spec.experimental and not bool(args.experimental):
        # Intent: experimental presets are opt-in because they add optional heavy deps/hardware assumptions.
        print(f"Error: preset '{preset_id}' is experimental. Re-run with --experimental.", file=sys.stderr)
        return EXIT_USAGE
    if not spec.graph.exists():
        print(f"Error: graph not found for preset '{preset_id}': {spec.graph}", file=sys.stderr)
        return EXIT_USAGE

    env = _build_env(repo_root=repo_root, spec=spec, args=args)

    if bool(args.validate_only):
        cmd = [sys.executable, "-m", "schnitzel_stream", "validate", "--graph", str(spec.graph)]
    else:
        cmd = [sys.executable, "-m", "schnitzel_stream", "--graph", str(spec.graph)]

    if args.max_events is not None:
        if int(args.max_events) <= 0:
            print("Error: --max-events must be > 0", file=sys.stderr)
            return EXIT_USAGE
        cmd.extend(["--max-events", str(int(args.max_events))])

    print(f"preset={preset_id}")
    print(f"graph={spec.graph}")
    print(f"validate_only={bool(args.validate_only)}")
    print(f"command={_shell_cmd(cmd)}")

    code = _run_subprocess(cmd=cmd, cwd=repo_root, env=env)
    if code != 0:
        # Intent: runtime/validator failures should collapse to one stable non-zero code for operator scripts.
        return EXIT_RUN_FAILED
    return EXIT_OK


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
