from __future__ import annotations

"""
Graph model (Phase 1 draft).

Intent:
- Keep the node/edge spec minimal and stable for v2 runtime.
- Future phases may extend ports/config typing without breaking existing graphs.
- This file is intentionally minimal and forward-compatible (ports/config exist but
  are not yet enforced by a runtime).
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NodeSpec:
    """A node instance in a graph."""

    node_id: str
    plugin: str
    kind: str = "node"  # source|node|sink (provisional)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeSpec:
    """A connection between nodes."""

    src: str
    dst: str
    src_port: str | None = None
    dst_port: str | None = None
