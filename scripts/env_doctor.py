#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/professor_showcase_guide.md
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import importlib
import json
import sys
from typing import Sequence

MIN_PYTHON = (3, 11)
REQUIRED_MODULES = ("omegaconf", "numpy", "pandas", "requests")
OPTIONAL_MODULES = ("cv2",)


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


def run_checks() -> list[CheckResult]:
    out = [_check_python()]
    out.extend(_check_import(name, required=True) for name in REQUIRED_MODULES)
    out.extend(_check_import(name, required=False) for name in OPTIONAL_MODULES)
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
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checks = run_checks()
    summary = _summary(checks)
    code = _exit_code(checks, strict=bool(args.strict))

    payload = {
        "tool": "env_doctor",
        "strict": bool(args.strict),
        "status": "ok" if code == 0 else "failed",
        "summary": summary,
        "checks": [asdict(item) for item in checks],
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
        return int(code)

    print("== Environment Doctor ==")
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
