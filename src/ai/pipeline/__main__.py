from __future__ import annotations

"""
Deprecated legacy CLI entrypoint.

Intent:
- `python -m schnitzel_stream` is the single supported entrypoint as of Phase 0.
- We keep this module in place to provide a clear error message instead of a
  generic Python import error.
"""


def main() -> int:
    raise SystemExit(
        "Legacy entrypoint is disabled: `python -m ai.pipeline`\n"
        "\n"
        "Use the universal platform entrypoint instead:\n"
        "  python -m schnitzel_stream --dry-run --max-events 5\n"
        "\n"
        "Docs:\n"
        "  docs/implementation/90-packaging/entrypoint/design.md\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())

