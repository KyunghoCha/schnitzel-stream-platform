from __future__ import annotations

"""
schnitzel_stream

Stream processing runtime (core package).

Status:
- Stable CLI/graph entrypoint lives under `schnitzel_stream.cli`.
- Node graph execution is the active runtime path.
"""

__all__ = ["__version__"]

# Keep a local version string for logs/docs. (No packaging metadata yet.)
__version__ = "0.1.0-rc.1"
