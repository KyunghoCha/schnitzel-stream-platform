from __future__ import annotations

"""
schnitzel_stream

Universal stream processing platform (core package).

Status:
- Stable CLI/graph entrypoint lives under `schnitzel_stream.cli`.
- Graph execution is v2 node-graph only (legacy v1 runtime removed from main tree).
"""

__all__ = ["__version__"]

# Keep a local version string for logs/docs. (No packaging metadata yet.)
__version__ = "0.1.0-rc.1"
