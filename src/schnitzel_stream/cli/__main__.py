from __future__ import annotations

"""
CLI entrypoint.

Intent:
- `python -m schnitzel_stream` is the stable entrypoint for the repo.
- Node graph specs are the active graph format.
- The default graph spec path is resolved from the repo root, not CWD, to keep
  behavior stable across edge devices, Docker, and subprocess tests.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from schnitzel_stream.control.throttle import FixedBudgetThrottle
from schnitzel_stream.graph.spec import ensure_node_graph_spec, load_node_graph_spec
from schnitzel_stream.graph.validate import validate_graph
from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.plugins.registry import PluginPolicy
from schnitzel_stream.project import resolve_project_root
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def _default_graph_path() -> Path:
    # Intent:
    # - Keep this graph dependency-light so `python -m schnitzel_stream` runs on most edges.
    return resolve_project_root() / "configs" / "graphs" / "dev_vision_e2e_mock.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schnitzel_stream",
        description="Stream processing runtime.",
        epilog="Alias: `schnitzel_stream validate ...` is equivalent to `--validate-only`.",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=str(_default_graph_path()),
        help="path to graph spec YAML (default: repo configs/graphs/dev_vision_e2e_mock.yaml)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate graph spec and exit without running",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="print a JSON run report",
    )

    parser.add_argument("--max-events", type=int, default=None, help="limit emitted events")
    return parser


def main(argv: list[str] | None = None) -> int:
    # Intent:
    # - Keep a simple flag-based CLI for node graph runtime.
    # - Also support a UX-friendly `validate` alias without introducing subparsers.
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    if argv and argv[0] == "validate":
        argv = argv[1:]
        if "--validate-only" not in argv:
            argv.append("--validate-only")

    parser = _build_parser()
    args = parser.parse_args(argv)

    ensure_node_graph_spec(args.graph)
    spec2 = load_node_graph_spec(args.graph)
    validate_graph(spec2.nodes, spec2.edges, allow_cycles=False)
    policy = PluginPolicy.from_env()
    registry = PluginRegistry(policy=policy)
    validate_graph_compat(spec2.nodes, spec2.edges, transport="inproc", registry=registry)
    if args.validate_only:
        return 0

    runner = InProcGraphRunner(registry=registry)
    # Intent: keep `--max-events` as a generic packet budget for node graphs
    # (counts source-emitted packets, not backend-acked events).
    throttle = FixedBudgetThrottle(max_source_emits_total=args.max_events) if args.max_events is not None else None
    result = runner.run(nodes=spec2.nodes, edges=spec2.edges, throttle=throttle)
    produced = sum(len(v) for v in result.outputs_by_node.values())
    if args.report_json:
        report = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "engine": "inproc",
            "graph_format": "node_graph",
            "graph": str(args.graph),
            "metrics": result.metrics,
        }
        print(json.dumps(report, separators=(",", ":"), default=str))
    else:
        print(f"node graph executed (in-proc): nodes={len(spec2.nodes)} edges={len(spec2.edges)} packets={produced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
