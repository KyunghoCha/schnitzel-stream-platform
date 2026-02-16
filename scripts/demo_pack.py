#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md, docs/guides/professor_showcase_guide.md
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_VALIDATE_FAILED = 2
EXIT_WEBCAM_FAILED = 20
COMMAND_TIMEOUT_SEC = 120.0
REPORT_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    graphs: tuple[Path, ...]
    webcam_required: bool = False


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_report_path(repo_root: Path) -> Path:
    return repo_root / "outputs" / "reports" / "demo_pack_latest.json"


def _build_scenarios(profile: str, repo_root: Path) -> list[Scenario]:
    scenarios = [
        Scenario(
            scenario_id="S1",
            title="inproc baseline",
            graphs=(repo_root / "configs" / "graphs" / "showcase_inproc_v2.yaml",),
        ),
        Scenario(
            scenario_id="S2",
            title="durable enqueue + drain/ack",
            graphs=(
                repo_root / "configs" / "graphs" / "showcase_durable_enqueue_v2.yaml",
                repo_root / "configs" / "graphs" / "showcase_durable_drain_ack_v2.yaml",
            ),
        ),
    ]
    if profile == "professor":
        scenarios.append(
            Scenario(
                scenario_id="S3",
                title="webcam pipeline",
                graphs=(repo_root / "configs" / "graphs" / "showcase_webcam_v2.yaml",),
                webcam_required=True,
            )
        )
    return scenarios


def _tail_text(text: str, *, max_lines: int = 20) -> str:
    lines = str(text or "").splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def _run_command(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> CommandResult:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SEC,
        )
        duration = time.monotonic() - started
        return CommandResult(
            returncode=int(proc.returncode),
            stdout=str(proc.stdout),
            stderr=str(proc.stderr),
            duration_sec=float(duration),
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        # Intent: fail-fast instead of hanging forever when a scenario cannot make progress.
        return CommandResult(
            returncode=124,
            stdout=str(exc.stdout or ""),
            stderr=f"command timed out after {COMMAND_TIMEOUT_SEC:.0f}s",
            duration_sec=float(duration),
        )


def _shell_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def _step_payload(*, phase: str, graph: Path, cmd: list[str], result: CommandResult) -> dict[str, object]:
    return {
        "phase": phase,
        "graph": str(graph),
        "command": _shell_cmd(cmd),
        "returncode": int(result.returncode),
        "duration_sec": round(float(result.duration_sec), 4),
        "stdout_tail": _tail_text(result.stdout),
        "stderr_tail": _tail_text(result.stderr),
    }


def _classify_failure(
    *,
    phase: str,
    result: CommandResult,
    webcam_required: bool,
    profile: str,
) -> tuple[str, str]:
    merged = f"{result.stdout}\n{result.stderr}".lower()
    if "no module named" in merged or "modulenotfounderror" in merged:
        return "environment", "dependency_missing"
    if result.returncode == 124:
        return phase, "command_timeout"
    if phase == "validate":
        return "validate", "validate_failed"
    if webcam_required and profile == "professor":
        return "run", "webcam_runtime_failed"
    return "run", "runtime_failed"


def _phase_status(item: dict[str, object], phase: str) -> str:
    steps = item.get("steps", [])
    if not isinstance(steps, list):
        return "n/a"
    phase_steps = [s for s in steps if isinstance(s, dict) and s.get("phase") == phase]
    if not phase_steps:
        return "n/a"
    return "ok" if all(s.get("returncode") == 0 for s in phase_steps) else "failed"


def _resolve_report_path(raw: str, *, repo_root: Path) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


def _reset_showcase_queue(queue_path: Path) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    if queue_path.exists():
        # Intent: reset showcase queue before each run so the durable demo stays deterministic.
        queue_path.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reproducible showcase scenarios for demos")
    parser.add_argument("--profile", choices=("ci", "professor"), required=True, help="Showcase profile")
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam device index for professor profile")
    parser.add_argument("--max-events", type=int, default=50, help="Max source emits per graph run")
    parser.add_argument(
        "--report",
        default="",
        help="JSON report path (default: outputs/reports/demo_pack_latest.json)",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if int(args.camera_index) < 0:
        print("Error: --camera-index must be >= 0", file=sys.stderr)
        return EXIT_RUN_FAILED
    if int(args.max_events) <= 0:
        print("Error: --max-events must be > 0", file=sys.stderr)
        return EXIT_RUN_FAILED

    repo_root = _repo_root()
    report_path = _resolve_report_path(args.report, repo_root=repo_root) if args.report else _default_report_path(repo_root)
    scenarios = _build_scenarios(str(args.profile), repo_root)

    queue_path = (repo_root / "outputs" / "queues" / "showcase_demo.sqlite3").resolve()
    _reset_showcase_queue(queue_path)

    env = dict(os.environ)
    py_path = str((repo_root / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{existing}" if existing else py_path
    env["SS_SHOWCASE_QUEUE_PATH"] = str(queue_path)
    env["SS_DEMO_CAMERA_INDEX"] = str(int(args.camera_index))

    report: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "profile": str(args.profile),
        "status": "ok",
        "exit_code": EXIT_OK,
        "queue_path": str(queue_path),
        "options": {
            "camera_index": int(args.camera_index),
            "max_events": int(args.max_events),
            "report": str(report_path),
        },
        "scenarios": [],
    }

    exit_code = EXIT_OK
    for scenario in scenarios:
        scenario_report: dict[str, object] = {
            "id": scenario.scenario_id,
            "title": scenario.title,
            "status": "ok",
            "steps": [],
        }

        for graph in scenario.graphs:
            validate_cmd = [sys.executable, "-m", "schnitzel_stream", "validate", "--graph", str(graph)]
            if not graph.exists():
                fail = CommandResult(
                    returncode=127,
                    stdout="",
                    stderr=f"graph not found: {graph}",
                    duration_sec=0.0,
                )
                scenario_report["steps"].append(_step_payload(phase="validate", graph=graph, cmd=validate_cmd, result=fail))
                scenario_report["status"] = "failed"
                scenario_report["failure_kind"] = "validate"
                scenario_report["failure_reason"] = "graph_not_found"
                exit_code = EXIT_VALIDATE_FAILED
                break

            validate_result = _run_command(validate_cmd, cwd=repo_root, env=env)
            scenario_report["steps"].append(
                _step_payload(phase="validate", graph=graph, cmd=validate_cmd, result=validate_result)
            )
            if validate_result.returncode != 0:
                scenario_report["status"] = "failed"
                failure_kind, failure_reason = _classify_failure(
                    phase="validate",
                    result=validate_result,
                    webcam_required=scenario.webcam_required,
                    profile=str(args.profile),
                )
                scenario_report["failure_kind"] = failure_kind
                scenario_report["failure_reason"] = failure_reason
                exit_code = EXIT_VALIDATE_FAILED
                break

        if scenario_report["status"] == "ok":
            for graph in scenario.graphs:
                run_cmd = [
                    sys.executable,
                    "-m",
                    "schnitzel_stream",
                    "--graph",
                    str(graph),
                    "--max-events",
                    str(int(args.max_events)),
                ]
                run_result = _run_command(run_cmd, cwd=repo_root, env=env)
                scenario_report["steps"].append(_step_payload(phase="run", graph=graph, cmd=run_cmd, result=run_result))
                if run_result.returncode != 0:
                    scenario_report["status"] = "failed"
                    failure_kind, failure_reason = _classify_failure(
                        phase="run",
                        result=run_result,
                        webcam_required=scenario.webcam_required,
                        profile=str(args.profile),
                    )
                    scenario_report["failure_kind"] = failure_kind
                    scenario_report["failure_reason"] = failure_reason
                    if scenario.webcam_required and str(args.profile) == "professor":
                        exit_code = EXIT_WEBCAM_FAILED
                    else:
                        exit_code = EXIT_RUN_FAILED
                    break

        cast_list = report["scenarios"]
        assert isinstance(cast_list, list)
        cast_list.append(scenario_report)

        if scenario_report["status"] != "ok":
            report["status"] = "failed"
            break

    scenarios_payload = report["scenarios"]
    assert isinstance(scenarios_payload, list)
    scenarios_total = len(scenarios_payload)
    scenarios_passed = sum(1 for item in scenarios_payload if isinstance(item, dict) and item.get("status") == "ok")
    report["summary"] = {
        "scenarios_total": scenarios_total,
        "scenarios_passed": scenarios_passed,
        "scenarios_failed": scenarios_total - scenarios_passed,
    }
    report["exit_code"] = int(exit_code)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"profile={args.profile}")
    for item in scenarios_payload:
        if isinstance(item, dict):
            validate_state = _phase_status(item, "validate")
            run_state = _phase_status(item, "run")
            line = (
                f"{item.get('id')} status={item.get('status')} "
                f"validate={validate_state} run={run_state} title={item.get('title')}"
            )
            if item.get("status") != "ok":
                line += f" failure_kind={item.get('failure_kind')} failure_reason={item.get('failure_reason')}"
            print(line)
    print(f"report={report_path}")
    print(f"exit_code={exit_code}")

    return int(exit_code)


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
