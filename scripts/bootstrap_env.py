#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_USAGE = 2
SCHEMA_VERSION = 1


def shell_cmd(cmd: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in cmd)


def run_cmd(cmd: list[str], *, cwd: Path, dry_run: bool, echo: bool = True) -> int:
    if echo:
        print(f"$ {shell_cmd(cmd)}")
    if dry_run:
        return 0
    proc = subprocess.run(cmd, cwd=str(cwd))
    return int(proc.returncode)


def _which(name: str) -> str | None:
    return shutil.which(name)


def _conda_env_exists(env_name: str) -> bool:
    proc = subprocess.run(["conda", "env", "list", "--json"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False
    envs = payload.get("envs", [])
    if not isinstance(envs, list):
        return False
    name_lower = str(env_name).strip().lower()
    for raw in envs:
        p = Path(str(raw))
        if p.name.strip().lower() == name_lower:
            return True
    return False


def choose_manager(raw: str) -> str:
    manager = str(raw or "auto").strip().lower()
    if manager not in {"auto", "conda", "pip"}:
        raise ValueError("--manager must be one of: auto, conda, pip")
    if manager != "auto":
        return manager
    return "conda" if _which("conda") else "pip"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dependency bootstrap helper (Conda + pip dual path)")
    parser.add_argument("--profile", choices=("base", "console", "yolo"), default="base")
    parser.add_argument("--manager", choices=("auto", "conda", "pip"), default="auto")
    parser.add_argument("--env-name", default="schnitzel-stream")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument(
        "--skip-doctor",
        action="store_true",
        help="Skip env_doctor execution (installation steps only)",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable bootstrap result")
    return parser.parse_args(argv)


def _doctor_profile(profile: str) -> str:
    if profile in {"console", "yolo"}:
        return profile
    return "base"


def _doctor_cmd_for_pip(*, profile: str) -> list[str]:
    return [
        sys.executable,
        "scripts/env_doctor.py",
        "--profile",
        _doctor_profile(profile),
        "--strict",
        "--json",
    ]


def _commands_for_pip(*, profile: str, skip_doctor: bool) -> list[list[str]]:
    cmds: list[list[str]] = [
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-r", "requirements-dev.txt"],
    ]
    if profile == "yolo":
        cmds.append([sys.executable, "-m", "pip", "install", "-r", "requirements-model.txt"])
    if profile == "console":
        cmds.append(["npm", "ci", "--prefix", "apps/stream-console"])
    if not skip_doctor:
        cmds.append(_doctor_cmd_for_pip(profile=profile))
    return cmds


def _doctor_cmd_for_conda(*, env_name: str, profile: str) -> list[str]:
    return [
        "conda",
        "run",
        "-n",
        env_name,
        "python",
        "scripts/env_doctor.py",
        "--profile",
        _doctor_profile(profile),
        "--strict",
        "--json",
    ]


def _commands_for_conda(*, profile: str, env_name: str, dry_run: bool, skip_doctor: bool) -> list[list[str]]:
    if not _which("conda"):
        raise RuntimeError("conda not found in PATH; rerun with --manager pip or install conda")

    env_exists = _conda_env_exists(env_name) if not dry_run else False
    cmds: list[list[str]] = []
    if env_exists:
        cmds.append(["conda", "env", "update", "-n", env_name, "-f", "environment.yml", "--prune"])
    else:
        cmds.append(["conda", "env", "create", "-n", env_name, "-f", "environment.yml"])

    if profile == "yolo":
        cmds.append(["conda", "run", "-n", env_name, "python", "-m", "pip", "install", "-r", "requirements-model.txt"])
    if profile == "console":
        cmds.append(["conda", "run", "-n", env_name, "npm", "ci", "--prefix", "apps/stream-console"])
    if not skip_doctor:
        cmds.append(_doctor_cmd_for_conda(env_name=env_name, profile=profile))
    return cmds


@dataclass(frozen=True)
class BootstrapStep:
    name: str
    command: str
    status: str
    return_code: int | None
    detail: str = ""


def _next_action(*, profile: str, manager: str, env_name: str, skip_doctor: bool, status: str) -> str:
    manager_val = str(manager).strip().lower()
    profile_val = _doctor_profile(profile)
    if manager_val == "conda":
        prefix = f"conda run -n {shlex.quote(str(env_name))}"
    else:
        prefix = "python"

    doctor_cmd = f"{prefix} scripts/env_doctor.py --profile {profile_val} --strict --json"
    up_cmd = f"{prefix} scripts/stream_console.py up --allow-local-mutations"

    if status == "failed":
        return doctor_cmd
    if skip_doctor:
        return doctor_cmd
    if profile == "console":
        return up_cmd
    return f"{prefix} scripts/stream_console.py doctor --strict --json"


def _payload(
    *,
    status: str,
    profile: str,
    manager_selected: str,
    dry_run: bool,
    steps: list[BootstrapStep],
    next_action: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": str(status),
        "profile": str(profile),
        "manager_selected": str(manager_selected),
        "dry_run": bool(dry_run),
        "steps": [asdict(item) for item in steps],
        "next_action": str(next_action),
    }


def _emit_result(*, args: argparse.Namespace, payload: dict[str, object], status_line: str) -> None:
    if bool(args.json):
        print(json.dumps(payload, separators=(",", ":")))
        return

    print(f"profile={args.profile}")
    print(f"manager={payload.get('manager_selected', '')}")
    print(f"env_name={args.env_name}")
    print(f"dry_run={bool(args.dry_run)}")
    print(f"status={status_line}")
    for item in payload.get("steps", []):
        if not isinstance(item, dict):
            continue
        print(
            f"[{item.get('status', 'unknown')}] "
            f"{item.get('name', 'step')} -> {item.get('command', '')}"
        )
    print(f"next_action={payload.get('next_action', '')}")


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manager = choose_manager(str(args.manager))
    except ValueError as exc:
        if bool(args.json):
            payload = _payload(
                status="usage_error",
                profile=str(args.profile),
                manager_selected="n/a",
                dry_run=bool(args.dry_run),
                steps=[],
                next_action="python scripts/bootstrap_env.py --help",
            )
            print(json.dumps(payload, separators=(",", ":")))
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    steps: list[BootstrapStep] = []
    next_action = _next_action(
        profile=str(args.profile),
        manager=manager,
        env_name=str(args.env_name),
        skip_doctor=bool(args.skip_doctor),
        status="ok",
    )

    if manager == "pip" and _which("npm") is None and str(args.profile) == "console" and not bool(args.dry_run):
        # Intent: dry-run should remain usable for planning in environments that do not yet have Node installed.
        steps.append(
            BootstrapStep(
                name="precheck:npm",
                command="npm --version",
                status="failed",
                return_code=127,
                detail="npm not found in PATH",
            )
        )
        payload = _payload(
            status="failed",
            profile=str(args.profile),
            manager_selected=manager,
            dry_run=bool(args.dry_run),
            steps=steps,
            next_action=next_action,
        )
        _emit_result(args=args, payload=payload, status_line="failed")
        print("Error: npm not found in PATH; install Node.js or use --manager conda", file=sys.stderr)
        return EXIT_RUNTIME

    try:
        if manager == "conda":
            cmds = _commands_for_conda(
                profile=str(args.profile),
                env_name=str(args.env_name),
                dry_run=bool(args.dry_run),
                skip_doctor=bool(args.skip_doctor),
            )
        else:
            cmds = _commands_for_pip(profile=str(args.profile), skip_doctor=bool(args.skip_doctor))
    except RuntimeError as exc:
        payload = _payload(
            status="failed",
            profile=str(args.profile),
            manager_selected=manager,
            dry_run=bool(args.dry_run),
            steps=steps,
            next_action=next_action,
        )
        _emit_result(args=args, payload=payload, status_line="failed")
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME

    if bool(args.skip_doctor):
        steps.append(
            BootstrapStep(
                name="doctor",
                command="env_doctor (strict/json)",
                status="skipped",
                return_code=None,
                detail="--skip-doctor enabled",
            )
        )

    for cmd in cmds:
        step_name = "install"
        if "env_doctor.py" in " ".join(cmd):
            step_name = "doctor"
        elif "npm" in cmd:
            step_name = "ui_install"

        code = run_cmd(cmd, cwd=PROJECT_ROOT, dry_run=bool(args.dry_run), echo=(not bool(args.json)))
        step_status = "executed" if code == 0 else "failed"
        if bool(args.dry_run):
            step_status = "planned"
        steps.append(
            BootstrapStep(
                name=step_name,
                command=shell_cmd(cmd),
                status=step_status,
                return_code=int(code),
            )
        )
        if code != 0:
            payload = _payload(
                status="failed",
                profile=str(args.profile),
                manager_selected=manager,
                dry_run=bool(args.dry_run),
                steps=steps,
                next_action=next_action,
            )
            _emit_result(args=args, payload=payload, status_line="failed")
            # Intent: keep a single runtime failure code for bootstrap automation.
            return EXIT_RUNTIME

    status = "ok"
    payload = _payload(
        status=status,
        profile=str(args.profile),
        manager_selected=manager,
        dry_run=bool(args.dry_run),
        steps=steps,
        next_action=next_action,
    )
    _emit_result(args=args, payload=payload, status_line=status)
    return EXIT_OK


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
