from __future__ import annotations

"""
Vision pack nodes.

Prefer these plugin paths over `schnitzel_stream.nodes.*`:
- `schnitzel_stream.packs.vision.nodes:OpenCvVideoFileSource`
- `schnitzel_stream.packs.vision.nodes:OpenCvRtspSource`
- `schnitzel_stream.packs.vision.nodes:OpenCvWebcamSource`
- `schnitzel_stream.packs.vision.nodes:EveryNthFrameSamplerNode`
- `schnitzel_stream.packs.vision.nodes:MockDetectorNode`
- `schnitzel_stream.packs.vision.nodes:YoloV8DetectorNode`
- `schnitzel_stream.packs.vision.nodes:OpenCvBboxDisplaySink`
- `schnitzel_stream.packs.vision.nodes:ProtocolV02EventBuilderNode`
- `schnitzel_stream.packs.vision.nodes:ZonePolicyNode`
- `schnitzel_stream.packs.vision.nodes:DedupPolicyNode`
"""

from schnitzel_stream.packs.vision.nodes.event_builder import ProtocolV02EventBuilderNode
from schnitzel_stream.packs.vision.nodes.mock_detection import MockDetectorNode
from schnitzel_stream.packs.vision.nodes.policy import DedupPolicyNode, ZonePolicyNode
from schnitzel_stream.packs.vision.nodes.video import (
    EveryNthFrameSamplerNode,
    OpenCvRtspSource,
    OpenCvVideoFileSource,
    OpenCvWebcamSource,
)
from schnitzel_stream.packs.vision.nodes.yolo import OpenCvBboxDisplaySink, YoloV8DetectorNode

__all__ = [
    "DedupPolicyNode",
    "EveryNthFrameSamplerNode",
    "MockDetectorNode",
    "OpenCvBboxDisplaySink",
    "OpenCvRtspSource",
    "OpenCvVideoFileSource",
    "OpenCvWebcamSource",
    "ProtocolV02EventBuilderNode",
    "YoloV8DetectorNode",
    "ZonePolicyNode",
]
