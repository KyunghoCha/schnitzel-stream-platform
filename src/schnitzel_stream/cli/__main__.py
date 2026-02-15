from __future__ import annotations

"""
CLI entrypoint (SSOT).

Intent:
- `python -m schnitzel_stream` is the new stable entrypoint for the repo.
- Only v2 node-graph specs are supported.
- The default graph spec path is resolved from the repo root, not CWD, to keep
  behavior stable across edge devices, Docker, and subprocess tests.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from schnitzel_stream.control.throttle import FixedBudgetThrottle
from schnitzel_stream.graph.spec import load_node_graph_spec, peek_graph_version
from schnitzel_stream.graph.validate import validate_graph
from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.plugins.registry import PluginPolicy
from schnitzel_stream.project import resolve_project_root
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def _default_graph_path() -> Path:
    # Intent:
    # - Phase 4 pivots the *default* graph to v2 to start deprecating the v1 legacy job graph.
    # - Keep this graph dependency-light so `python -m schnitzel_stream` runs on most edges.
    return resolve_project_root() / "configs" / "graphs" / "dev_vision_e2e_mock_v2.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schnitzel_stream",
        description="Universal stream processing platform (SSOT entrypoint).",
        epilog="Alias: `schnitzel_stream validate ...` is equivalent to `--validate-only`.",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=str(_default_graph_path()),
        help="path to graph spec YAML (default: repo configs/graphs/dev_vision_e2e_mock_v2.yaml)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate graph spec and exit without running",
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="print a JSON run report (v2 in-proc runtime only)",
    )

    # Intent: keep legacy flags parseable for wrapper script compatibility.
    # They are ignored by the v2 runtime path.
    parser.add_argument("--camera-id", type=str, default=None, help="camera id override")
    parser.add_argument("--video", type=str, default=None, help="mp4 file path override")
    parser.add_argument(
        "--source-type",
        type=str,
        choices=("file", "rtsp", "webcam", "plugin"),
        default=None,
        help="override source type",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="webcam device index override (default: camera config index or 0)",
    )
    parser.add_argument("--dry-run", action="store_true", help="do not post to backend")
    parser.add_argument("--output-jsonl", type=str, default=None, help="write events to jsonl file")
    parser.add_argument("--max-events", type=int, default=None, help="limit emitted events")
    parser.add_argument("--visualize", action="store_true", help="show debug window with detections")
    parser.add_argument("--loop", action="store_true", help="loop video file indefinitely")
    return parser


def _maybe_warn_ignored_legacy_flags(args: argparse.Namespace) -> None:
    if os.environ.get("SCHNITZEL_STREAM_SILENCE_CLI_COMPAT_WARNING"):
        return
    ignored: list[str] = []
    if args.camera_id is not None:
        ignored.append("--camera-id")
    if args.video is not None:
        ignored.append("--video")
    if args.source_type is not None:
        ignored.append("--source-type")
    if args.camera_index is not None:
        ignored.append("--camera-index")
    if args.dry_run:
        ignored.append("--dry-run")
    if args.output_jsonl is not None:
        ignored.append("--output-jsonl")
    if args.visualize:
        ignored.append("--visualize")
    if args.loop:
        ignored.append("--loop")
    if not ignored:
        return
    print(
        "WARNING: legacy compatibility flags are ignored in v2 runtime: "
        f"{', '.join(ignored)}. "
        "Use v2 graph/plugin config instead. "
        "Set SCHNITZEL_STREAM_SILENCE_CLI_COMPAT_WARNING=1 to silence this warning.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    # Intent:
    # - Keep backwards-compatible flag-based CLI.
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

    version = peek_graph_version(args.graph)
    if version != 2:
        raise ValueError(f"unsupported graph spec version: {version} (only v2 is supported)")

    spec2 = load_node_graph_spec(args.graph)
    validate_graph(spec2.nodes, spec2.edges, allow_cycles=False)
    policy = PluginPolicy.from_env()
    registry = PluginRegistry(policy=policy)
    validate_graph_compat(spec2.nodes, spec2.edges, transport="inproc", registry=registry)
    if args.validate_only:
        return 0

    _maybe_warn_ignored_legacy_flags(args)

    runner = InProcGraphRunner(registry=registry)
    # Intent: reuse legacy `--max-events` as a generic packet budget for v2 graphs
    # (counts source-emitted packets, not backend-acked events).
    throttle = FixedBudgetThrottle(max_source_emits_total=args.max_events) if args.max_events is not None else None
    result = runner.run(nodes=spec2.nodes, edges=spec2.edges, throttle=throttle)
    produced = sum(len(v) for v in result.outputs_by_node.values())
    if args.report_json:
        report = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "engine": "inproc",
            "graph_version": 2,
            "graph": str(args.graph),
            "metrics": result.metrics,
        }
        print(json.dumps(report, separators=(",", ":"), default=str))
    else:
        print(f"v2 graph executed (in-proc): nodes={len(spec2.nodes)} edges={len(spec2.edges)} packets={produced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
