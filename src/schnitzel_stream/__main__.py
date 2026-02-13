from __future__ import annotations

# `python -m schnitzel_stream` delegates to the CLI package.

from schnitzel_stream.cli.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())

