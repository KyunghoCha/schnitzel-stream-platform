from __future__ import annotations

"""
Phase 0 CLI entrypoint.

Intent:
- `python -m schnitzel_stream` is the new stable entrypoint for the repo.
- Phase 0 runs a single "job" described by a minimal graph spec file.
- The default graph spec path is resolved from the repo root, not CWD, to keep
  behavior stable across edge devices, Docker, and subprocess tests.
"""

import argparse
import sys
from pathlib import Path

from schnitzel_stream.graph.spec import load_graph_spec, load_node_graph_spec, peek_graph_version
from schnitzel_stream.graph.validate import validate_graph
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.plugins.registry import PluginPolicy
from schnitzel_stream.project import resolve_project_root
from schnitzel_stream.runtime.inproc import InProcGraphRunner


def _default_graph_path() -> Path:
    return resolve_project_root() / "configs" / "graphs" / "legacy_pipeline.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schnitzel_stream",
        description="Universal stream processing platform (Phase 0: legacy job runner).",
        epilog="Alias: `schnitzel_stream validate ...` is equivalent to `--validate-only`.",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=str(_default_graph_path()),
        help="path to graph spec YAML (default: repo configs/graphs/legacy_pipeline.yaml)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate graph spec and exit without running",
    )

    # Keep legacy pipeline flags as the Phase 0 compatibility surface.
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

    if version == 1:
        spec = load_graph_spec(args.graph)
        # Structural validation only; loading plugins is intentionally skipped here.
        PluginPolicy.from_env().ensure_path_allowed(spec.job)
        if args.validate_only:
            return 0

        registry = PluginRegistry()
        job = registry.load(spec.job)
        run = registry.require_callable(job, "run")
        run(spec, args)
        return 0

    if version == 2:
        spec2 = load_node_graph_spec(args.graph)
        validate_graph(spec2.nodes, spec2.edges, allow_cycles=False)
        policy = PluginPolicy.from_env()
        for node in spec2.nodes:
            policy.ensure_path_allowed(node.plugin)
        if args.validate_only:
            return 0

        runner = InProcGraphRunner(registry=PluginRegistry(policy=policy))
        result = runner.run(nodes=spec2.nodes, edges=spec2.edges)
        produced = sum(len(v) for v in result.outputs_by_node.values())
        print(f"v2 graph executed (in-proc): nodes={len(spec2.nodes)} edges={len(spec2.edges)} packets={produced}")
        return 0

    raise AssertionError(f"unreachable: unsupported version={version}")


if __name__ == "__main__":
    raise SystemExit(main())
