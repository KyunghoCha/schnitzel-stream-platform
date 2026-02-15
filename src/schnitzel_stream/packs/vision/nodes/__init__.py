from __future__ import annotations

"""
Vision pack nodes.

Prefer these plugin paths over `schnitzel_stream.nodes.*`:
- `schnitzel_stream.packs.vision.nodes:OpenCvVideoFileSource`
- `schnitzel_stream.packs.vision.nodes:EveryNthFrameSamplerNode`
- `schnitzel_stream.packs.vision.nodes:MockDetectorNode`
- `schnitzel_stream.packs.vision.nodes:ProtocolV02EventBuilderNode`
- `schnitzel_stream.packs.vision.nodes:ZonePolicyNode`
- `schnitzel_stream.packs.vision.nodes:DedupPolicyNode`
"""

from schnitzel_stream.packs.vision.nodes.event_builder import ProtocolV02EventBuilderNode
from schnitzel_stream.packs.vision.nodes.mock_detection import MockDetectorNode
from schnitzel_stream.packs.vision.nodes.policy import DedupPolicyNode, ZonePolicyNode
from schnitzel_stream.packs.vision.nodes.video import EveryNthFrameSamplerNode, OpenCvVideoFileSource

__all__ = [
    "DedupPolicyNode",
    "EveryNthFrameSamplerNode",
    "MockDetectorNode",
    "OpenCvVideoFileSource",
    "ProtocolV02EventBuilderNode",
    "ZonePolicyNode",
]

