#!/usr/bin/env python3
# Docs: docs/guides/lab_rc_release_checklist.md, docs/implementation/operations_release.md, docs/ops/command_reference.md
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    category: str
    command: list[str]


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    category: str
    command: list[str]
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run aggregated release readiness checks")
    parser.add_argument("--profile", required=True, help="Readiness profile (only: lab-rc)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    return parser.parse_args(argv)


def _tail(text: str, *, lines: int = 20) -> str:
    rows = str(text or "").splitlines()
    if not rows:
        return ""
    return "\n".join(rows[-lines:])


def _is_environment_failure(*, stdout: str, stderr: str) -> bool:
    merged = f"{stdout}\n{stderr}".lower()
    needles = (
        "no module named",
        "modulenotfounderror",
        "command not found",
        "is not recognized as an internal or external command",
        "cannot import",
    )
    return any(token in merged for token in needles)


def _build_checks(profile: str) -> list[CheckSpec]:
    normalized = str(profile or "").strip().lower()
    if normalized != "lab-rc":
        raise ValueError("--profile must be: lab-rc")

    python = sys.executable
    return [
        CheckSpec("compileall", "quality_gate", [python, "-m", "compileall", "-q", "src", "tests", "scripts"]),
        CheckSpec("docs_hygiene", "quality_gate", [python, "scripts/docs_hygiene.py", "--strict"]),
        CheckSpec(
            "test_hygiene",
            "quality_gate",
            [
                python,
                "scripts/test_hygiene.py",
                "--strict",
                "--max-duplicate-groups",
                "0",
                "--max-no-assert",
                "0",
                "--max-trivial-assert-true",
                "0",
            ],
        ),
        CheckSpec("reliability_smoke", "runtime", [python, "scripts/reliability_smoke.py", "--mode", "quick", "--json"]),
        CheckSpec(
            "control_policy_snapshot",
            "policy_drift",
            [
                python,
                "scripts/control_policy_snapshot.py",
                "--check",
                "--baseline",
                "configs/policy/control_api_policy_snapshot_v1.json",
            ],
        ),
        CheckSpec(
            "command_surface_snapshot",
            "surface_drift",
            [
                python,
                "scripts/command_surface_snapshot.py",
                "--check",
                "--baseline",
                "configs/policy/command_surface_snapshot_v1.json",
            ],
        ),
        CheckSpec("ssot_sync_check", "ssot_drift", [python, "scripts/ssot_sync_check.py", "--strict", "--json"]),
    ]


def _run_one(*, spec: CheckSpec, cwd: Path) -> CheckResult:
    env = dict(os.environ)
    src = str((cwd / "src").resolve())
    existing = str(env.get("PYTHONPATH", "") or "").strip()
    env["PYTHONPATH"] = f"{src}{os.pathsep}{existing}" if existing else src
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    started = time.monotonic()
    proc = subprocess.run(
        spec.command,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return CheckResult(
        check_id=spec.check_id,
        category=spec.category,
        command=list(spec.command),
        returncode=int(proc.returncode),
        duration_sec=float(time.monotonic() - started),
        stdout=str(proc.stdout or ""),
        stderr=str(proc.stderr or ""),
    )


def _result_payload(*, profile: str, results: list[CheckResult], exit_code: int) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for item in results:
        ok = int(item.returncode) == 0
        if ok:
            passed += 1
        else:
            failed += 1
        taxonomy = item.category
        if not ok and _is_environment_failure(stdout=item.stdout, stderr=item.stderr):
            # Intent: normalize dependency/toolchain failures under explicit env taxonomy for release triage.
            taxonomy = "env"

        checks.append(
            {
                "id": item.check_id,
                "taxonomy": taxonomy,
                "command": item.command,
                "returncode": int(item.returncode),
                "status": "passed" if ok else "failed",
                "duration_sec": round(float(item.duration_sec), 4),
                "stdout_tail": _tail(item.stdout),
                "stderr_tail": _tail(item.stderr),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "profile": str(profile),
        "checks": checks,
        "passed": int(passed),
        "failed": int(failed),
        "exit_code": int(exit_code),
    }


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile = str(args.profile or "").strip()

    try:
        specs = _build_checks(profile)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    cwd = _repo_root()
    results: list[CheckResult] = []
    has_failure = False
    for spec in specs:
        result = _run_one(spec=spec, cwd=cwd)
        results.append(result)
        if int(result.returncode) != 0:
            has_failure = True

    exit_code = EXIT_FAILED if has_failure else EXIT_OK
    payload = _result_payload(profile=profile, results=results, exit_code=exit_code)

    if bool(args.json):
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    else:
        print(f"profile={payload['profile']}")
        print(f"passed={payload['passed']} failed={payload['failed']} exit_code={payload['exit_code']}")
        for item in payload["checks"]:
            mark = "OK" if item["status"] == "passed" else "FAIL"
            print(
                f"[{mark}] {item['id']} taxonomy={item['taxonomy']} returncode={item['returncode']} duration_sec={item['duration_sec']}"
            )

    return exit_code


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
