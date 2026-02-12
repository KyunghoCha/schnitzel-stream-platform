from __future__ import annotations

from ai.vision.accuracy_eval import match_detections


def test_match_detections_tp_fp_fn() -> None:
    gt = [
        {"class_key": "A", "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}},
        {"class_key": "A", "bbox": {"x1": 20, "y1": 20, "x2": 30, "y2": 30}},
    ]
    preds = [
        {"class_key": "A", "bbox": {"x1": 1, "y1": 1, "x2": 11, "y2": 11}},  # match
        {"class_key": "A", "bbox": {"x1": 100, "y1": 100, "x2": 110, "y2": 110}},  # fp
    ]
    counts = match_detections(gt, preds, iou_thres=0.5)
    assert counts.tp == 1
    assert counts.fp == 1
    assert counts.fn == 1
