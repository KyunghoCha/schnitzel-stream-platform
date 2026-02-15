from __future__ import annotations

"""
DEPRECATED: vision nodes moved to `schnitzel_stream.packs.vision.nodes`.

Kept as a compatibility shim for older graphs that reference `schnitzel_stream.nodes.video:*`.
"""

from schnitzel_stream.packs.vision.nodes.video import EveryNthFrameSamplerNode, OpenCvVideoFileSource

__all__ = ["EveryNthFrameSamplerNode", "OpenCvVideoFileSource"]

