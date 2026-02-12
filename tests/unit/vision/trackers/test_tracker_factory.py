from __future__ import annotations

from ai.vision.trackers.tracker_factory import build_tracker
from ai.vision.trackers.tracker_iou import IOUTracker


def test_factory_iou() -> None:
    tracker = build_tracker("iou", max_age=5, min_hits=1, iou_thres=0.3)
    assert isinstance(tracker, IOUTracker)


def test_factory_unknown() -> None:
    tracker = build_tracker("unknown", max_age=5, min_hits=1, iou_thres=0.3)
    assert tracker is None
