#!/usr/bin/env python3
# scripts/stream_fleet.py
# Docs: docs/ops/command_reference.md
"""
Universal stream fleet launcher (cross-platform).
Start/stop/status management for per-stream v2 graph processes.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.ops import fleet as fleet_ops
from process_manager import is_process_running, start_process, stop_process


DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "schnitzel_stream_fleet_run")
DEFAULT_GRAPH_TEMPLATE = str(PROJECT_ROOT / "configs" / "graphs" / "dev_stream_template_v2.yaml")
DEFAULT_CONFIG = str(PROJECT_ROOT / "configs" / "fleet.yaml")


StreamSpec = fleet_ops.StreamSpec


def load_stream_specs(config_path: Path) -> list[StreamSpec]:
    """Load enabled stream specs from fleet config."""
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        specs = fleet_ops.load_stream_specs(config_path)
    except ImportError:
        print("Error: omegaconf is required. Run: pip install omegaconf", file=sys.stderr)
        sys.exit(1)
    return specs


def _resolve_stream_subset(specs: list[StreamSpec], raw_streams: str) -> list[StreamSpec]:
    return fleet_ops.resolve_stream_subset(specs, raw_streams)


def _resolve_input_plugin(spec: StreamSpec) -> str:
    return fleet_ops.resolve_input_plugin(spec)


def _stream_env(spec: StreamSpec) -> dict[str, str]:
    return fleet_ops.build_stream_env(spec, project_root=PROJECT_ROOT)


def cmd_start(args: argparse.Namespace) -> None:
    """Start graph processes for all selected streams."""
    config_path = Path(args.config)
    graph_template = Path(args.graph_template)
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not graph_template.exists():
        print(f"Error: graph template not found: {graph_template}", file=sys.stderr)
        sys.exit(1)

    specs = _resolve_stream_subset(load_stream_specs(config_path), args.streams)
    if not specs:
        print(f"Error: No enabled streams found in {config_path}", file=sys.stderr)
        sys.exit(1)

    print(f"log_dir={log_dir}")
    print(f"pid_dir={pid_dir}")
    print(f"graph_template={graph_template}")
    print(f"streams={','.join(spec.stream_id for spec in specs)}")

    lines = fleet_ops.start_streams(
        specs=specs,
        graph_template=graph_template,
        log_dir=log_dir,
        project_root=PROJECT_ROOT,
        extra_args=fleet_ops.split_extra_args(str(args.extra_args)),
        start_process_fn=start_process,
        is_process_running_fn=is_process_running,
        python_executable=sys.executable,
    )
    for line in lines:
        print(line)


def cmd_stop(args: argparse.Namespace) -> None:
    """Stop all managed stream processes."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    _stopped, lines = fleet_ops.stop_streams(pid_dir=pid_dir, stop_process_fn=stop_process)
    for line in lines:
        print(line)


def cmd_status(args: argparse.Namespace) -> None:
    """Show status of all managed stream processes."""
    log_dir = Path(args.log_dir)
    pid_dir = log_dir / "pids"

    if not pid_dir.exists():
        print(f"pid_dir not found: {pid_dir}")
        return

    _running, _total, lines = fleet_ops.status_streams(pid_dir=pid_dir, is_process_running_fn=is_process_running)
    for line in lines:
        print(line)


def build_parser(
    *,
    prog: str = "stream_fleet",
    default_config: str = DEFAULT_CONFIG,
    default_graph_template: str = DEFAULT_GRAPH_TEMPLATE,
    default_log_dir: str = DEFAULT_LOG_DIR,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Universal stream fleet launcher (cross-platform)", prog=prog)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start all stream graph processes")
    start_parser.add_argument(
        "--config",
        "-c",
        default=default_config,
        help="Path to fleet config file",
    )
    start_parser.add_argument(
        "--graph-template",
        default=default_graph_template,
        help="Path to v2 graph template used for each stream process",
    )
    start_parser.add_argument(
        "--log-dir",
        "-l",
        default=default_log_dir,
        help="Directory for logs and PID files",
    )
    start_parser.add_argument(
        "--streams",
        default="",
        help="Comma-separated stream IDs (overrides config selection)",
    )
    start_parser.add_argument(
        "--extra-args",
        default="",
        help="Extra args passed to runtime (for example '--max-events 100')",
    )
    start_parser.set_defaults(func=cmd_start)

    stop_parser = subparsers.add_parser("stop", help="Stop all stream graph processes")
    stop_parser.add_argument(
        "--log-dir",
        "-l",
        default=default_log_dir,
        help="Directory for logs and PID files",
    )
    stop_parser.set_defaults(func=cmd_stop)

    status_parser = subparsers.add_parser("status", help="Show status of all stream graph processes")
    status_parser.add_argument(
        "--log-dir",
        "-l",
        default=default_log_dir,
        help="Directory for logs and PID files",
    )
    status_parser.set_defaults(func=cmd_status)

    return parser


def run(
    argv: list[str] | None = None,
    *,
    prog: str = "stream_fleet",
    default_config: str = DEFAULT_CONFIG,
    default_graph_template: str = DEFAULT_GRAPH_TEMPLATE,
    default_log_dir: str = DEFAULT_LOG_DIR,
) -> int:
    parser = build_parser(
        prog=prog,
        default_config=default_config,
        default_graph_template=default_graph_template,
        default_log_dir=default_log_dir,
    )
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
