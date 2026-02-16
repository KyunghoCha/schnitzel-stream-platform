#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/professor_showcase_guide.md
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import importlib
import json
from pathlib import Path
import sys
from typing import Sequence

MIN_PYTHON = (3, 11)
BASE_REQUIRED_MODULES = ("omegaconf", "numpy", "pandas", "requests")
BASE_OPTIONAL_MODULES = ("cv2",)
YOLO_REQUIRED_MODULES = ("ultralytics", "torch")


@dataclass(frozen=True)
class CheckResult:
    name: str
    required: bool
    ok: bool
    detail: str


def _python_version_info() -> tuple[int, int, int]:
    vi = sys.version_info
    return int(vi.major), int(vi.minor), int(vi.micro)


def _check_python() -> CheckResult:
    major, minor, micro = _python_version_info()
    ok = (major, minor) >= MIN_PYTHON
    detail = f"detected={major}.{minor}.{micro} required>={MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    return CheckResult(name="python", required=True, ok=ok, detail=detail)


def _check_import(module_name: str, *, required: bool) -> CheckResult:
    try:
        importlib.import_module(module_name)
        return CheckResult(name=module_name, required=required, ok=True, detail="import ok")
    except Exception as exc:  # pragma: no cover - exact import errors are environment-specific
        return CheckResult(name=module_name, required=required, ok=False, detail=str(exc))


def _check_torch_cuda() -> CheckResult:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        return CheckResult(name="torch_cuda", required=False, ok=False, detail=f"torch import failed: {exc}")

    try:
        available = bool(torch.cuda.is_available())
        count = int(torch.cuda.device_count())
        cuda_ver = getattr(torch.version, "cuda", None)
        detail = f"available={available} device_count={count} torch_cuda={cuda_ver}"
        return CheckResult(name="torch_cuda", required=False, ok=available, detail=detail)
    except Exception as exc:
        return CheckResult(name="torch_cuda", required=False, ok=False, detail=f"cuda probe failed: {exc}")


def _check_model_path(path: Path) -> CheckResult:
    target = Path(path).resolve()
    ok = target.exists()
    detail = f"path={target}"
    if not ok:
        detail += " (not found)"
    return CheckResult(name="yolo_model_path", required=False, ok=ok, detail=detail)


def _check_webcam_probe(*, camera_index: int, enabled: bool) -> CheckResult:
    if not enabled:
        return CheckResult(
            name="webcam_probe",
            required=False,
            ok=True,
            detail="probe skipped (set --probe-webcam to test camera open)",
        )

    try:
        cv2 = importlib.import_module("cv2")
    except Exception as exc:
        return CheckResult(name="webcam_probe", required=False, ok=False, detail=f"cv2 import failed: {exc}")

    if not hasattr(cv2, "VideoCapture"):
        return CheckResult(name="webcam_probe", required=False, ok=False, detail="cv2.VideoCapture not available")

    try:
        cap = cv2.VideoCapture(int(camera_index))
        opened = bool(cap.isOpened())
        cap.release()
    except Exception as exc:
        return CheckResult(name="webcam_probe", required=False, ok=False, detail=f"probe exception: {exc}")

    return CheckResult(
        name="webcam_probe",
        required=False,
        ok=opened,
        detail=f"camera_index={int(camera_index)} opened={opened}",
    )


def run_checks(
    *,
    profile: str,
    model_path: Path,
    camera_index: int,
    probe_webcam: bool,
) -> list[CheckResult]:
    out = [_check_python()]
    out.extend(_check_import(name, required=True) for name in BASE_REQUIRED_MODULES)
    out.extend(_check_import(name, required=False) for name in BASE_OPTIONAL_MODULES)

    if profile == "yolo":
        out.extend(_check_import(name, required=True) for name in YOLO_REQUIRED_MODULES)
        out.append(_check_torch_cuda())
        out.append(_check_model_path(model_path))
    elif profile == "webcam":
        out.append(_check_webcam_probe(camera_index=int(camera_index), enabled=bool(probe_webcam)))

    return out


def _exit_code(checks: Sequence[CheckResult], *, strict: bool) -> int:
    if not strict:
        return 0
    return 1 if any(item.required and not item.ok for item in checks) else 0


def _summary(checks: Sequence[CheckResult]) -> dict[str, int]:
    required_total = sum(1 for item in checks if item.required)
    required_failed = sum(1 for item in checks if item.required and not item.ok)
    optional_total = sum(1 for item in checks if not item.required)
    optional_failed = sum(1 for item in checks if (not item.required) and (not item.ok))
    return {
        "required_total": int(required_total),
        "required_failed": int(required_failed),
        "optional_total": int(optional_total),
        "optional_failed": int(optional_failed),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Environment checks for schnitzel-stream-platform runtime")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when required checks fail")
    parser.add_argument("--json", action="store_true", help="Print checks as JSON only")
    parser.add_argument(
        "--profile",
        choices=("base", "yolo", "webcam"),
        default="base",
        help="Check profile (base runtime / yolo stack / webcam readiness)",
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

    payload = {
        "tool": "env_doctor",
        "profile": str(args.profile),
        "strict": bool(args.strict),
        "status": "ok" if code == 0 else "failed",
        "summary": summary,
        "checks": [asdict(item) for item in checks],
    }

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
