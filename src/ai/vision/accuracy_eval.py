# Docs: docs/ops/ai/accuracy_validation.md
# 오프라인 평가 헬퍼; 라이브 파이프라인 런타임에서는 사용되지 않음.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.vision.geometry import iou_bbox_dict as iou


@dataclass
class EvalCounts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def precision(self) -> float:
        denom = self.tp + self.fp
        return 0.0 if denom == 0 else self.tp / denom

    def recall(self) -> float:
        denom = self.tp + self.fn
        return 0.0 if denom == 0 else self.tp / denom


def match_detections(
    gt: list[dict[str, Any]],
    preds: list[dict[str, Any]],
    iou_thres: float,
) -> EvalCounts:
    # 동일 클래스 키 내에서 IoU 기준 그리디 매칭
    counts = EvalCounts()
    used = set()
    for g in gt:
        best_iou = 0.0
        best_idx = None
        for i, p in enumerate(preds):
            if i in used:
                continue
            if g["class_key"] != p["class_key"]:
                continue
            val = iou(g["bbox"], p["bbox"])
            if val > best_iou:
                best_iou = val
                best_idx = i
        if best_idx is not None and best_iou >= iou_thres:
            counts.tp += 1
            used.add(best_idx)
        else:
            counts.fn += 1
    counts.fp += len(preds) - len(used)
    return counts


def merge_counts(dst: dict[str, EvalCounts], src: dict[str, EvalCounts]) -> None:
    for k, v in src.items():
        if k not in dst:
            dst[k] = EvalCounts()
        dst[k].tp += v.tp
        dst[k].fp += v.fp
        dst[k].fn += v.fn
