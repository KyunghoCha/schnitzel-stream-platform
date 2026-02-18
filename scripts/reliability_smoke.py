#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/implementation/testing_quality.md
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_USAGE = 2
SCHEMA_VERSION = 1

_QUICK_TARGETS = (
    "tests/unit/test_sqlite_queue.py",
    "tests/unit/nodes/test_durable_sqlite_nodes.py",
    "tests/integration/test_durable_queue_replay.py",
    "tests/integration/test_durable_queue_reliability.py",
)

_FULL_TARGETS = (
    *_QUICK_TARGETS,
    "tests/integration/test_v2_durable_queue_idempotency_e2e.py",
)


@dataclass(frozen=True)
class SmokeResult:
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _targets_for_mode(mode: str) -> tuple[str, ...]:
    normalized = str(mode or "").strip().lower()
    if normalized == "quick":
        return _QUICK_TARGETS
    if normalized == "full":
        return _FULL_TARGETS
    raise ValueError("--mode must be one of: quick, full")


def _run_pytest(*, cwd: Path, targets: tuple[str, ...]) -> SmokeResult:
    cmd = [sys.executable, "-m", "pytest", "-q", *targets]
    env = dict(os.environ)
    src_path = str((cwd / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing}" if existing else src_path
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    started = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = time.monotonic() - started
    return SmokeResult(
        returncode=int(proc.returncode),
        stdout=str(proc.stdout or ""),
        stderr=str(proc.stderr or ""),
        duration_sec=float(duration),
    )


def _extract_stat(pattern: str, text: str) -> int:
    match = re.search(pattern, text)
    if not match:
        return 0
    return int(match.group(1))


def _summary(*, mode: str, targets: tuple[str, ...], result: SmokeResult) -> dict[str, object]:
    merged = f"{result.stdout}\n{result.stderr}"
    passed = _extract_stat(r"(\d+)\s+passed", merged)
    failed = _extract_stat(r"(\d+)\s+failed", merged)
    errors = _extract_stat(r"(\d+)\s+error", merged)
    failed_total = int(failed + errors)

    if result.returncode != 0 and failed_total == 0:
        # Intent: preserve deterministic failure accounting even when pytest cannot run (missing dependency, import error).
        failed_total = 1

    tests_total = int(passed + failed_total)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": str(mode),
        "targets": list(targets),
        "tests_total": tests_total,
        "passed": int(passed),
        "failed": int(failed_total),
        "returncode": int(result.returncode),
        "duration_sec": round(float(result.duration_sec), 4),
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run durable reliability smoke checks")
    parser.add_argument("--mode", default="quick", help="Smoke mode: quick or full")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mode = str(args.mode or "").strip().lower()
    try:
        targets = _targets_for_mode(mode)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    result = _run_pytest(cwd=_repo_root(), targets=targets)
    payload = _summary(mode=mode, targets=targets, result=result)

    if bool(args.json):
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    else:
        print(f"mode={payload['mode']}")
        print(f"tests_total={payload['tests_total']} passed={payload['passed']} failed={payload['failed']}")
        print(f"duration_sec={payload['duration_sec']}")
        print(f"returncode={payload['returncode']}")
        if payload["stdout_tail"]:
            print("stdout_tail:")
            print(str(payload["stdout_tail"]))
        if payload["stderr_tail"]:
            print("stderr_tail:")
            print(str(payload["stderr_tail"]))

    return EXIT_OK if int(result.returncode) == 0 else EXIT_RUNTIME


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
