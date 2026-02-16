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

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stream_fleet


def run(argv: list[str] | None = None) -> int:
    print(
        "Notice: `scripts/multi_cam.py` is a legacy alias. "
        "Use `python scripts/stream_fleet.py ...` instead.",
        file=sys.stderr,
    )
    return stream_fleet.run(argv, prog="multi_cam")


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
