from __future__ import annotations

from ai.vision.trackers.tracker_iou import IOUTracker


def test_iou_tracker_stable_id() -> None:
    tracker = IOUTracker(max_age=2, min_hits=1, iou_thres=0.3)
    dets1 = [
        {"object_type": "PERSON", "bbox": {"x1": 10, "y1": 10, "x2": 50, "y2": 50}},
    ]
    out1 = tracker.update(dets1)
    tid1 = out1[0].get("track_id")
    assert tid1 is not None

    dets2 = [
        {"object_type": "PERSON", "bbox": {"x1": 12, "y1": 12, "x2": 52, "y2": 52}},
    ]
    out2 = tracker.update(dets2)
    tid2 = out2[0].get("track_id")
    assert tid2 == tid1


def test_iou_tracker_new_id_when_far() -> None:
    tracker = IOUTracker(max_age=2, min_hits=1, iou_thres=0.5)
    dets1 = [
        {"object_type": "PERSON", "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}},
    ]
    out1 = tracker.update(dets1)
    tid1 = out1[0].get("track_id")
    dets2 = [
        {"object_type": "PERSON", "bbox": {"x1": 100, "y1": 100, "x2": 120, "y2": 120}},
    ]
    out2 = tracker.update(dets2)
    tid2 = out2[0].get("track_id")
    assert tid2 != tid1
