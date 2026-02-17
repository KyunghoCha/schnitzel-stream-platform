#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Add script and src paths for direct execution.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from process_manager import is_process_running, start_process, stop_process
from schnitzel_stream.ops import console as console_ops
from schnitzel_stream.ops import envcheck as env_ops


EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_USAGE = 2


def _validate_port(raw: int, *, name: str) -> int:
    port = int(raw)
    if port <= 0 or port > 65535:
        raise ValueError(f"{name} must be in range 1..65535")
    return port


def _status_lines(payload: dict[str, object]) -> list[str]:
    api = payload.get("api", {})
    ui = payload.get("ui", {})
    if not isinstance(api, dict):
        api = {}
    if not isinstance(ui, dict):
        ui = {}
    api_health = api.get("health", {})
    if not isinstance(api_health, dict):
        api_health = {}

    lines = [
        f"ready={payload.get('ready', False)}",
        f"log_dir={payload.get('log_dir', '')}",
        (
            "api: "
            f"status={api.get('status', 'unknown')} "
            f"running={api.get('running', False)} "
            f"port_open={api.get('port_open', False)} "
            f"health_reason={api_health.get('reason', 'n/a')} "
            f"health_code={api_health.get('status_code', 'n/a')}"
        ),
        (
            "ui: "
            f"status={ui.get('status', 'unknown')} "
            f"running={ui.get('running', False)} "
            f"port_open={ui.get('port_open', False)}"
        ),
    ]
    return lines


def _doctor_result(*, strict: bool, json_out: bool) -> int:
    checks = env_ops.run_checks(
        profile="console",
        model_path=Path("models/yolov8n.pt"),
        camera_index=0,
        probe_webcam=False,
    )
    payload = env_ops.payload(profile="console", strict=bool(strict), checks=checks)
    code = int(env_ops.exit_code(checks, strict=bool(strict)))
    if json_out:
        print(json.dumps(payload, separators=(",", ":")))
        return code

    print("== Stream Console Doctor ==")
    for item in checks:
        mark = "OK" if item.ok else ("ERROR" if item.required else "WARN")
        req = "required" if item.required else "optional"
        print(f"[{mark}] {item.name} ({req}) - {item.detail}")
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        print(
            "summary: "
            f"required_failed={summary.get('required_failed', 0)}/{summary.get('required_total', 0)} "
            f"optional_failed={summary.get('optional_failed', 0)}/{summary.get('optional_total', 0)}"
        )
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-command local stream console launcher")
    sub = parser.add_subparsers(dest="command", required=True)

    up = sub.add_parser("up", help="Start local API/UI console stack")
    up.add_argument("--api-host", default=console_ops.DEFAULT_API_HOST)
    up.add_argument("--api-port", type=int, default=console_ops.DEFAULT_API_PORT)
    up.add_argument("--ui-host", default=console_ops.DEFAULT_UI_HOST)
    up.add_argument("--ui-port", type=int, default=console_ops.DEFAULT_UI_PORT)
    up.add_argument("--log-dir", default=console_ops.DEFAULT_LOG_DIR)
    up.add_argument("--allow-local-mutations", action="store_true")
    up.add_argument("--token", default="", help="Set SS_CONTROL_API_TOKEN in API process env")
    scope = up.add_mutually_exclusive_group()
    scope.add_argument("--api-only", action="store_true")
    scope.add_argument("--ui-only", action="store_true")

    status = sub.add_parser("status", help="Show local API/UI console status")
    status.add_argument("--log-dir", default=console_ops.DEFAULT_LOG_DIR)
    status.add_argument("--json", action="store_true")

    down = sub.add_parser("down", help="Stop local API/UI console stack")
    down.add_argument("--log-dir", default=console_ops.DEFAULT_LOG_DIR)

    doctor = sub.add_parser("doctor", help="Run console environment checks")
    doctor.add_argument("--strict", action="store_true")
    doctor.add_argument("--json", action="store_true")

    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = PROJECT_ROOT.resolve()

    try:
        if args.command == "doctor":
            return _doctor_result(strict=bool(args.strict), json_out=bool(args.json))

        paths = console_ops.resolve_console_paths(repo_root=repo_root, log_dir=str(args.log_dir))

        if args.command == "up":
            api_port = _validate_port(int(args.api_port), name="--api-port")
            ui_port = _validate_port(int(args.ui_port), name="--ui-port")
            actions = console_ops.start_selected_services(
                repo_root=repo_root,
                paths=paths,
                python_executable=sys.executable,
                api_host=str(args.api_host),
                api_port=api_port,
                ui_host=str(args.ui_host),
                ui_port=ui_port,
                allow_local_mutations=bool(args.allow_local_mutations),
                token=str(args.token),
                api_only=bool(args.api_only),
                ui_only=bool(args.ui_only),
                start_process_fn=start_process,
                is_process_running_fn=is_process_running,
            )
            for item in actions:
                print(
                    f"{item.get('service', 'unknown')}: "
                    f"{item.get('action', 'unknown')} "
                    f"pid={item.get('pid', 'n/a')}"
                )
            status = console_ops.collect_status(paths=paths, is_process_running_fn=is_process_running)
            for line in _status_lines(status):
                print(line)
            return EXIT_OK if bool(status.get("ready", False)) else EXIT_RUNTIME

        if args.command == "status":
            payload = console_ops.collect_status(paths=paths, is_process_running_fn=is_process_running)
            if bool(args.json):
                print(json.dumps(payload, separators=(",", ":"), default=str))
            else:
                for line in _status_lines(payload):
                    print(line)
            return EXIT_OK

        if args.command == "down":
            actions = console_ops.stop_all_services(paths=paths, stop_process_fn=stop_process)
            for item in actions:
                print(
                    f"{item.get('service', 'unknown')}: "
                    f"{item.get('action', 'unknown')} "
                    f"pid={item.get('pid', 'n/a')}"
                )
            return EXIT_OK

        print(f"Error: unknown command: {args.command}", file=sys.stderr)
        return EXIT_USAGE
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Exception as exc:
        # Intent: lifecycle commands should fail loudly with one stable runtime code for automation.
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
