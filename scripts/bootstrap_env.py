#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
from __future__ import annotations

import argparse
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


def shell_cmd(cmd: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in cmd)


def run_cmd(cmd: list[str], *, cwd: Path, dry_run: bool) -> int:
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
    return parser.parse_args(argv)


def _doctor_profile(profile: str) -> str:
    if profile in {"console", "yolo"}:
        return profile
    return "base"


def _commands_for_pip(*, profile: str) -> list[list[str]]:
    cmds: list[list[str]] = [
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-r", "requirements-dev.txt"],
    ]
    if profile == "yolo":
        cmds.append([sys.executable, "-m", "pip", "install", "-r", "requirements-model.txt"])
    if profile == "console":
        cmds.append(["npm", "ci", "--prefix", "apps/stream-console"])

    cmds.append(
        [
            sys.executable,
            "scripts/env_doctor.py",
            "--profile",
            _doctor_profile(profile),
            "--strict",
            "--json",
        ]
    )
    return cmds


def _commands_for_conda(*, profile: str, env_name: str, dry_run: bool) -> list[list[str]]:
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

    cmds.append(
        [
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
    )
    return cmds


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manager = choose_manager(str(args.manager))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(f"profile={args.profile}")
    print(f"manager={manager}")
    print(f"env_name={args.env_name}")
    print(f"dry_run={bool(args.dry_run)}")

    if manager == "pip" and _which("npm") is None and str(args.profile) == "console":
        print("Error: npm not found in PATH; install Node.js or use --manager conda", file=sys.stderr)
        return EXIT_RUNTIME

    try:
        if manager == "conda":
            cmds = _commands_for_conda(
                profile=str(args.profile),
                env_name=str(args.env_name),
                dry_run=bool(args.dry_run),
            )
        else:
            cmds = _commands_for_pip(profile=str(args.profile))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME

    for cmd in cmds:
        code = run_cmd(cmd, cwd=PROJECT_ROOT, dry_run=bool(args.dry_run))
        if code != 0:
            # Intent: keep a single runtime failure code for bootstrap automation.
            return EXIT_RUNTIME

    return EXIT_OK


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
