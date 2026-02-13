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
from pathlib import Path

from schnitzel_stream.graph.spec import load_graph_spec
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.project import resolve_project_root


def _default_graph_path() -> Path:
    return resolve_project_root() / "configs" / "graphs" / "legacy_pipeline.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schnitzel_stream",
        description="Universal stream processing platform (Phase 0: legacy job runner).",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=str(_default_graph_path()),
        help="path to graph spec YAML (default: repo configs/graphs/legacy_pipeline.yaml)",
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
    parser = _build_parser()
    args = parser.parse_args(argv)

    spec = load_graph_spec(args.graph)
    if spec.version != 1:
        raise ValueError(f"unsupported graph spec version: {spec.version} (supported: 1)")

    registry = PluginRegistry()
    job = registry.load(spec.job)
    run = registry.require_callable(job, "run")
    run(spec, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

