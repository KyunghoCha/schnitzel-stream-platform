# Model Accuracy Validation Guide

## English
Purpose
-------
Define a lightweight accuracy validation workflow for detection models.
This is *framework-agnostic* and can be used with YOLO/ONNX outputs.

Scope
-----
- Validate detection accuracy before deployment.
- Track per-class precision/recall and false positives.
- Separate validation for Phase 1 vs Phase 2 classes.

Phase 0: Dataset Readiness
--------------------------
1. Collect labeled frames (or short clips) with ground truth boxes.
2. Ensure labels align with `docs/packs/vision/model_class_taxonomy.md`.
3. Split into train/val/test sets (at least val/test for evaluation).
4. Prepare GT JSONL (one line per image):
```json
{"image_path": "data/val/img_001.jpg", "labels": [{"class_id": 0, "bbox": [10, 20, 200, 260]}]}
```

Phase 1: Metrics
----------------
- Precision / Recall
- mAP@0.5 (minimum)
- mAP@0.5:0.95 (optional)
- Per-class confusion summary

Phase 2: Threshold Tuning
-------------------------
1. Sweep confidence threshold (e.g., 0.1 → 0.9).
2. Choose per-class threshold if necessary.
3. Validate on separate holdout set.

Phase 3: Acceptance Criteria (draft)
------------------------------------
- PERSON: precision >= 0.90, recall >= 0.85
- FIRE/SMOKE: precision >= 0.80, recall >= 0.70
- PPE/POSTURE: precision >= 0.85, recall >= 0.80

Artifacts
---------
- `metrics_summary.json`
- confusion tables per class
- threshold config used for deployment

Status
------
- Guide only. Requires labeled dataset and project policy lock.

Run (template)
--------------
```bash
PYTHONPATH=src python scripts/accuracy_eval.py \
  --gt data/labels/val.jsonl \
  --adapter ai.vision.yolo_adapter:YOLOAdapter \
  --class-map configs/model_class_map.yaml \
  --conf 0.25 --iou 0.5 \
  --out metrics_summary.json
```

Related Docs
------------
- Class taxonomy: `docs/packs/vision/model_class_taxonomy.md`
- Model interface: `docs/packs/vision/model_interface.md`

## 한국어
목적
-----
탐지 모델의 정확도 검증 워크플로를 정의한다.
프레임워크 종속성이 없으며 YOLO/ONNX 결과에 공통 적용 가능하다.

범위
-----
- 배포 전 정확도 검증
- 클래스별 precision/recall 및 false positive 추적
- Phase 1/2 클래스 분리 검증

Phase 0: 데이터셋 준비
----------------------
1. GT 박스가 있는 라벨링 데이터 수집(프레임/클립).
2. 라벨이 `docs/packs/vision/model_class_taxonomy.md`와 일치하는지 확인.
3. train/val/test 분리(최소 val/test 필요).
4. GT JSONL 준비(이미지당 한 줄):
```json
{"image_path": "data/val/img_001.jpg", "labels": [{"class_id": 0, "bbox": [10, 20, 200, 260]}]}
```

Phase 1: 지표
-------------
- Precision / Recall
- mAP@0.5 (최소 기준)
- mAP@0.5:0.95 (선택)
- 클래스별 혼동 요약

Phase 2: 임계값 튜닝
--------------------
1. confidence threshold sweep (0.1 → 0.9)
2. 필요 시 클래스별 threshold 결정
3. holdout 세트로 재검증

Phase 3: 수용 기준(초안)
------------------------
- PERSON: precision >= 0.90, recall >= 0.85
- FIRE/SMOKE: precision >= 0.80, recall >= 0.70
- PPE/POSTURE: precision >= 0.85, recall >= 0.80

산출물
------
- `metrics_summary.json`
- 클래스별 혼동표
- 배포용 threshold 설정

상태
-----
- 가이드 문서이며, 데이터셋/프로젝트 정책 확정 필요.

실행 예시(템플릿)
----------------
```bash
PYTHONPATH=src python scripts/accuracy_eval.py \
  --gt data/labels/val.jsonl \
  --adapter ai.vision.yolo_adapter:YOLOAdapter \
  --class-map configs/model_class_map.yaml \
  --conf 0.25 --iou 0.5 \
  --out metrics_summary.json
```

관련 문서
---------
- 클래스 분류: `docs/packs/vision/model_class_taxonomy.md`
- 모델 인터페이스: `docs/packs/vision/model_interface.md`
