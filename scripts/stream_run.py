#!/usr/bin/env python3
# scripts/stream_run.py
# Docs: docs/ops/command_reference.md
"""
One-command preset launcher for common v2 stream workflows.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess
import sys


EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class PresetSpec:
    preset_id: str
    description: str
    graph: Path
    experimental: bool = False
    env_defaults: dict[str, str] | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_input_path(raw: str, *, repo_root: Path) -> str:
    p = Path(raw)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    return str(p)


def _preset_table(repo_root: Path) -> dict[str, PresetSpec]:
    graphs = repo_root / "configs" / "graphs"
    return {
        "inproc_demo": PresetSpec(
            preset_id="inproc_demo",
            description="Minimal in-proc packet flow demo",
            graph=graphs / "dev_inproc_demo_v2.yaml",
        ),
        "file_frames": PresetSpec(
            preset_id="file_frames",
            description="Video-file source + frame sampler + print sink",
            graph=graphs / "dev_video_file_frames_v2.yaml",
            env_defaults={
                "SS_INPUT_PATH": str((repo_root / "data" / "samples" / "2048246-hd_1920_1080_24fps.mp4").resolve()),
                "SS_INPUT_LOOP": "false",
            },
        ),
        "webcam_frames": PresetSpec(
            preset_id="webcam_frames",
            description="Webcam source + frame sampler + print sink",
            graph=graphs / "dev_webcam_frames_v2.yaml",
            env_defaults={"SS_CAMERA_INDEX": "0"},
        ),
        "file_yolo": PresetSpec(
            preset_id="file_yolo",
            description="Video-file YOLO overlay (loop + low-latency queue policy)",
            graph=graphs / "dev_video_file_yolo_overlay_v2.yaml",
            experimental=True,
            env_defaults={
                "SS_INPUT_PATH": str((repo_root / "data" / "samples" / "2048246-hd_1920_1080_24fps.mp4").resolve()),
                "SS_YOLO_MODEL_PATH": str((repo_root / "models" / "yolov8n.pt").resolve()),
                "SS_YOLO_DEVICE": "cpu",
                "SS_INPUT_LOOP": "true",
            },
        ),
        "webcam_yolo": PresetSpec(
            preset_id="webcam_yolo",
            description="Webcam YOLO overlay",
            graph=graphs / "dev_webcam_yolo_overlay_v2.yaml",
            experimental=True,
            env_defaults={
                "SS_CAMERA_INDEX": "0",
                "SS_YOLO_MODEL_PATH": str((repo_root / "models" / "yolov8n.pt").resolve()),
                "SS_YOLO_DEVICE": "cpu",
            },
        ),
    }


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


def _list_presets(*, table: dict[str, PresetSpec], include_experimental: bool) -> int:
    print("preset_id\texperimental\tgraph\tdescription")
    for preset_id in sorted(table):
        spec = table[preset_id]
        if spec.experimental and not include_experimental:
            continue
        mark = "yes" if spec.experimental else "no"
        print(f"{spec.preset_id}\t{mark}\t{spec.graph}\t{spec.description}")
    if not include_experimental:
        print("hint: add --experimental to list opt-in presets")
    return EXIT_OK


def _build_env(*, repo_root: Path, spec: PresetSpec, args: argparse.Namespace) -> dict[str, str]:
    env = dict(os.environ)
    py_path = str((repo_root / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{existing}" if existing else py_path

    for key, value in (spec.env_defaults or {}).items():
        env.setdefault(str(key), str(value))

    if args.input_path:
        env["SS_INPUT_PATH"] = _resolve_input_path(str(args.input_path), repo_root=repo_root)
    if args.camera_index is not None:
        env["SS_CAMERA_INDEX"] = str(int(args.camera_index))
    if args.device:
        env["SS_YOLO_DEVICE"] = str(args.device)
    if args.loop:
        env["SS_INPUT_LOOP"] = str(args.loop)

    return env


def _shell_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def _run_subprocess(*, cmd: list[str], cwd: Path, env: dict[str, str]) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env)
    return int(proc.returncode)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()
    table = _preset_table(repo_root)

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
