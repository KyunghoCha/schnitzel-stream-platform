#!/usr/bin/env python3
# Docs: docs/packs/vision/ops/ai/accuracy_validation.md
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2

from ai.pipeline.model_adapter import load_model_adapter
from ai.vision.accuracy_eval import match_detections, merge_counts, EvalCounts
from ai.vision.class_mapping import load_class_map


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="경량 정확도 평가 도구")
    p.add_argument("--gt", required=True, help="정답 데이터셋 (jsonl)")
    p.add_argument("--adapter", required=True, help="모델 어댑터 경로 (module:Class)")
    p.add_argument("--class-map", default=None, help="클래스 매핑 yaml (선택)")
    p.add_argument("--conf", type=float, default=0.25, help="confidence 임계값")
    p.add_argument("--iou", type=float, default=0.5, help="IoU 임계값")
    p.add_argument("--out", default="metrics_summary.json", help="결과 json 출력 경로")
    return p.parse_args()


def _class_key_from_map(class_map: dict[int, Any], class_id: int) -> str | None:
    entry = class_map.get(class_id)
    if entry is None:
        return None
    return f"{entry.event_type}:{entry.object_type}"


def _class_key_from_pred(pred: dict[str, Any]) -> str:
    return f"{pred.get('event_type')}:{pred.get('object_type')}"


def main() -> None:
    args = _parse_args()
    gt_path = Path(args.gt)
    adapter = load_model_adapter(args.adapter)
    class_map = load_class_map(args.class_map)

    per_class: dict[str, EvalCounts] = {}
    total = EvalCounts()

    with gt_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            image_path = row.get("image_path")
            labels = row.get("labels", [])
            if not image_path:
                continue
            img = cv2.imread(image_path)
            if img is None:
                continue
            preds = adapter.infer(img) or []
            if isinstance(preds, dict):
                preds = [preds]

            pred_items: list[dict[str, Any]] = []
            for p in preds:
                if not isinstance(p, dict):
                    continue
                if float(p.get("confidence", 0.0)) < args.conf:
                    continue
                bbox = p.get("bbox")
                if not isinstance(bbox, dict):
                    continue
                pred_items.append(
                    {
                        "class_key": _class_key_from_pred(p),
                        "bbox": bbox,
                    }
                )

            gt_items: list[dict[str, Any]] = []
            for g in labels:
                if not isinstance(g, dict):
                    continue
                cid = g.get("class_id")
                bbox = g.get("bbox")
                if cid is None or not isinstance(bbox, list) or len(bbox) != 4:
                    continue
                key = _class_key_from_map(class_map, int(cid))
                if key is None:
                    continue
                gt_items.append(
                    {
                        "class_key": key,
                        "bbox": {"x1": int(bbox[0]), "y1": int(bbox[1]), "x2": int(bbox[2]), "y2": int(bbox[3])},
                    }
                )

            # 클래스별 집계
            local: dict[str, EvalCounts] = {}
            for key in {g["class_key"] for g in gt_items} | {p["class_key"] for p in pred_items}:
                gt_k = [g for g in gt_items if g["class_key"] == key]
                pr_k = [p for p in pred_items if p["class_key"] == key]
                local[key] = match_detections(gt_k, pr_k, args.iou)
            # 클래스별 집계(per_class, local)
            merge_counts(per_class, local)
            total.tp += sum(v.tp for v in local.values())
            total.fp += sum(v.fp for v in local.values())
            total.fn += sum(v.fn for v in local.values())

    out = {
        "overall": {"precision": total.precision(), "recall": total.recall(), "tp": total.tp, "fp": total.fp, "fn": total.fn},
        "per_class": {
            k: {"precision": v.precision(), "recall": v.recall(), "tp": v.tp, "fp": v.fp, "fn": v.fn}
            for k, v in per_class.items()
        },
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
