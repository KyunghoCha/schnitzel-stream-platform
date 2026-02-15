from __future__ import annotations

"""
DEPRECATED: vision nodes moved to `schnitzel_stream.packs.vision.nodes`.

Kept as a compatibility shim for older graphs that reference `schnitzel_stream.nodes.mock_detection:*`.
"""

from schnitzel_stream.packs.vision.nodes.mock_detection import MockDetectorNode

__all__ = ["MockDetectorNode"]

