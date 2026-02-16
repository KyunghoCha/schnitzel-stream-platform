#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import sys

# Add project src path for direct script execution.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run stream control API server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=18700, help="Bind port (default: 18700)")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if int(args.port) <= 0 or int(args.port) > 65535:
        print("Error: --port must be in range 1..65535", file=sys.stderr)
        return 2

    try:
        import uvicorn
    except Exception as exc:
        print(f"Error: uvicorn is required ({exc})", file=sys.stderr)
        print("Install with: pip install fastapi uvicorn", file=sys.stderr)
        return 1

    from schnitzel_stream.control_api import create_app

    app = create_app()
    # Intent: local-only default host limits accidental remote exposure unless caller opts in explicitly.
    uvicorn.run(app, host=str(args.host), port=int(args.port), log_level="info")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
