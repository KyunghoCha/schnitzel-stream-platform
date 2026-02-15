from __future__ import annotations

"""
DEPRECATED: vision nodes moved to `schnitzel_stream.packs.vision.nodes`.

Kept as a compatibility shim for older graphs that reference `schnitzel_stream.nodes.policy:*`.
"""

from schnitzel_stream.packs.vision.nodes.policy import DedupPolicyNode, ZonePolicyNode

__all__ = ["DedupPolicyNode", "ZonePolicyNode"]

