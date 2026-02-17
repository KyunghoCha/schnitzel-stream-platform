from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from pathlib import Path
import shutil
import sys
from typing import Sequence


MIN_PYTHON = (3, 11)
BASE_REQUIRED_MODULES = ("omegaconf", "numpy", "pandas", "requests")
BASE_OPTIONAL_MODULES = ("cv2",)
YOLO_REQUIRED_MODULES = ("ultralytics", "torch")
CONSOLE_REQUIRED_MODULES = ("fastapi", "uvicorn")


@dataclass(frozen=True)
class CheckResult:
    name: str
    required: bool
    ok: bool
    detail: str


def python_version_info() -> tuple[int, int, int]:
    vi = sys.version_info
    return int(vi.major), int(vi.minor), int(vi.micro)


def check_python() -> CheckResult:
    major, minor, micro = python_version_info()
    ok = (major, minor) >= MIN_PYTHON
    detail = f"detected={major}.{minor}.{micro} required>={MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    return CheckResult(name="python", required=True, ok=ok, detail=detail)


def check_import(module_name: str, *, required: bool) -> CheckResult:
    try:
        importlib.import_module(module_name)
        return CheckResult(name=module_name, required=required, ok=True, detail="import ok")
    except Exception as exc:  # pragma: no cover - exact import errors are environment-specific
        return CheckResult(name=module_name, required=required, ok=False, detail=str(exc))


def check_torch_cuda() -> CheckResult:
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


def check_model_path(path: Path) -> CheckResult:
    target = Path(path).resolve()
    ok = target.exists()
    detail = f"path={target}"
    if not ok:
        detail += " (not found)"
    return CheckResult(name="yolo_model_path", required=False, ok=ok, detail=detail)


def check_executable(name: str, *, required: bool, install_hint: str = "") -> CheckResult:
    path = shutil.which(name)
    if path:
        return CheckResult(name=f"exe:{name}", required=required, ok=True, detail=f"found at {path}")
    hint = f" not found; {install_hint}".strip() if install_hint else " not found"
    return CheckResult(name=f"exe:{name}", required=required, ok=False, detail=hint)


def check_webcam_probe(*, camera_index: int, enabled: bool) -> CheckResult:
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
    out = [check_python()]
    out.extend(check_import(name, required=True) for name in BASE_REQUIRED_MODULES)
    out.extend(check_import(name, required=False) for name in BASE_OPTIONAL_MODULES)

    if profile == "yolo":
        out.extend(check_import(name, required=True) for name in YOLO_REQUIRED_MODULES)
        out.append(check_torch_cuda())
        out.append(check_model_path(model_path))
    elif profile == "console":
        out.extend(check_import(name, required=True) for name in CONSOLE_REQUIRED_MODULES)
        out.append(
            check_executable(
                "node",
                required=True,
                install_hint="install Node.js LTS from https://nodejs.org/",
            )
        )
        out.append(
            check_executable(
                "npm",
                required=True,
                install_hint="install Node.js (npm is bundled) and reopen your terminal",
            )
        )
    elif profile == "webcam":
        out.append(check_webcam_probe(camera_index=int(camera_index), enabled=bool(probe_webcam)))

    return out


def exit_code(checks: Sequence[CheckResult], *, strict: bool) -> int:
    if not strict:
        return 0
    return 1 if any(item.required and not item.ok for item in checks) else 0


def summary(checks: Sequence[CheckResult]) -> dict[str, int]:
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


def payload(*, profile: str, strict: bool, checks: Sequence[CheckResult]) -> dict[str, object]:
    code = exit_code(checks, strict=bool(strict))
    return {
        "tool": "env_doctor",
        "profile": str(profile),
        "strict": bool(strict),
        "status": "ok" if code == 0 else "failed",
        "summary": summary(checks),
        "checks": [asdict(item) for item in checks],
    }
