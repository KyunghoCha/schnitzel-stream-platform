#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/professor_showcase_guide.md
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
from typing import Sequence

# Add project src path for direct script execution.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.ops import envcheck as env_ops

MIN_PYTHON = env_ops.MIN_PYTHON
BASE_REQUIRED_MODULES = env_ops.BASE_REQUIRED_MODULES
BASE_OPTIONAL_MODULES = env_ops.BASE_OPTIONAL_MODULES
YOLO_REQUIRED_MODULES = env_ops.YOLO_REQUIRED_MODULES
CheckResult = env_ops.CheckResult


def _python_version_info() -> tuple[int, int, int]:
    vi = sys.version_info
    return int(vi.major), int(vi.minor), int(vi.micro)


def _check_python() -> CheckResult:
    env_ops.python_version_info = _python_version_info
    return env_ops.check_python()


def _check_import(module_name: str, *, required: bool) -> CheckResult:
    env_ops.importlib = importlib
    return env_ops.check_import(module_name, required=required)


def _check_torch_cuda() -> CheckResult:
    env_ops.importlib = importlib
    return env_ops.check_torch_cuda()


def _check_model_path(path: Path) -> CheckResult:
    return env_ops.check_model_path(path)


def _check_webcam_probe(*, camera_index: int, enabled: bool) -> CheckResult:
    env_ops.importlib = importlib
    return env_ops.check_webcam_probe(camera_index=camera_index, enabled=enabled)


def run_checks(
    *,
    profile: str,
    model_path: Path,
    camera_index: int,
    probe_webcam: bool,
) -> list[CheckResult]:
    env_ops.python_version_info = _python_version_info
    env_ops.importlib = importlib
    return env_ops.run_checks(
        profile=str(profile),
        model_path=Path(model_path),
        camera_index=int(camera_index),
        probe_webcam=bool(probe_webcam),
    )


def _exit_code(checks: Sequence[CheckResult], *, strict: bool) -> int:
    return env_ops.exit_code(checks, strict=strict)


def _summary(checks: Sequence[CheckResult]) -> dict[str, int]:
    return env_ops.summary(checks)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Environment checks for schnitzel-stream-platform runtime")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when required checks fail")
    parser.add_argument("--json", action="store_true", help="Print checks as JSON only")
    parser.add_argument(
        "--profile",
        choices=("base", "yolo", "webcam", "console"),
        default="base",
        help="Check profile (base runtime / yolo stack / webcam readiness / console stack)",
    )
    parser.add_argument(
        "--model-path",
        default="models/yolov8n.pt",
        help="Model path hint for yolo profile",
    )
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index hint for webcam profile")
    parser.add_argument("--probe-webcam", action="store_true", help="Try opening webcam device in webcam profile")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checks = run_checks(
        profile=str(args.profile),
        model_path=Path(str(args.model_path)),
        camera_index=int(args.camera_index),
        probe_webcam=bool(args.probe_webcam),
    )
    summary = _summary(checks)
    code = _exit_code(checks, strict=bool(args.strict))

    payload = env_ops.payload(profile=str(args.profile), strict=bool(args.strict), checks=checks)

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
        return int(code)

    print("== Environment Doctor ==")
    print(f"profile={args.profile}")
    for item in checks:
        if item.ok:
            mark = "OK"
        elif item.required:
            mark = "ERROR"
        else:
            mark = "WARN"
        req = "required" if item.required else "optional"
        print(f"[{mark}] {item.name} ({req}) - {item.detail}")
    print(
        "summary: "
        f"required_failed={summary['required_failed']}/{summary['required_total']} "
        f"optional_failed={summary['optional_failed']}/{summary['optional_total']}"
    )
    if code != 0:
        # Intent: strict mode is used by CI gates to fail early on missing runtime dependencies.
        print("strict check failed: one or more required checks did not pass", file=sys.stderr)
    return int(code)


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
