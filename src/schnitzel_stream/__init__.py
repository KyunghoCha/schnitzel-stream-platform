from __future__ import annotations

"""
schnitzel_stream

Universal stream processing platform (core package).

Phase 0: Strangler migration.
- New CLI/graph entrypoint lives under `schnitzel_stream.cli`.
- Legacy CCTV pipeline remains under `ai.*` modules but is no longer executed via `python -m ai.pipeline`.
"""

__all__ = ["__version__"]

# Keep a local version string for logs/docs. (No packaging metadata yet.)
__version__ = "0.1.0"

