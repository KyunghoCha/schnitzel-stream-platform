from __future__ import annotations

from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve repo root path deterministically.

    Intent:
    - Avoid relying on CWD so subprocess tests and Docker runs behave the same.
    - Keep the heuristic simple for Phase 0: `src/schnitzel_stream/...` -> repo root.
    """
    return Path(__file__).resolve().parents[2]

