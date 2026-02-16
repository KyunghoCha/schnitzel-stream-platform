#!/usr/bin/env python3
# scripts/multi_cam.py
# Docs: docs/ops/command_reference.md
"""
Legacy alias for stream fleet operations.

Intent:
- Keep backward-compatible command entrypoint for one transition cycle.
- Redirect users to `scripts/stream_fleet.py` as the primary interface.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stream_fleet

LEGACY_DEFAULT_CONFIG = str(SCRIPT_DIR.parent / "configs" / "cameras.yaml")
LEGACY_DEFAULT_GRAPH_TEMPLATE = str(SCRIPT_DIR.parent / "configs" / "graphs" / "dev_camera_template_v2.yaml")
LEGACY_DEFAULT_LOG_DIR = str(Path(tempfile.gettempdir()) / "ai_pipeline_multi_cam_run")


def run(argv: list[str] | None = None) -> int:
    print(
        "Notice: `scripts/multi_cam.py` is a legacy alias. "
        "Use `python scripts/stream_fleet.py ...` instead.",
        file=sys.stderr,
    )
    return stream_fleet.run(
        argv,
        prog="multi_cam",
        default_config=LEGACY_DEFAULT_CONFIG,
        default_graph_template=LEGACY_DEFAULT_GRAPH_TEMPLATE,
        default_log_dir=LEGACY_DEFAULT_LOG_DIR,
    )


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
