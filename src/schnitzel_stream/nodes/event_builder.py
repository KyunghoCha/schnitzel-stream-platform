from __future__ import annotations

"""
DEPRECATED: vision nodes moved to `schnitzel_stream.packs.vision.nodes`.

Kept as a compatibility shim for older graphs that reference `schnitzel_stream.nodes.event_builder:*`.
"""

from schnitzel_stream.packs.vision.nodes.event_builder import ProtocolV02EventBuilderNode, build_event_scaffold

__all__ = ["ProtocolV02EventBuilderNode", "build_event_scaffold"]

