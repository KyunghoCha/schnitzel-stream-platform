# Model Training Plan

## English
Purpose
-------
Define a practical, execution-friendly plan to build and validate a production model for the safety CCTV pipeline. This document is the source of truth for data collection, labeling, training, evaluation, and deployment steps.

Scope
-----
- Required classes (phase 1): PERSON, ZONE_INTRUSION, DANGER_ZONE_ENTRY.
- Optional classes (phase 2+): PPE, POSTURE, SMOKE, FIRE, HAZARD.
- Any new class beyond protocol v0.2 requires protocol update and policy confirmation.

Assumptions
-----------
- Hardware target is not fixed (GPU/Jetson/CPU-only).
- Resolution/FPS/latency targets are TBD.
- Budget target: ~KRW 1,000,000 (draft).
- Backend integration will accept protocol v0.2 payloads.

Data Collection
---------------
- Collect representative footage from target environments (day/night, indoor/outdoor, weather variations).
- Include edge cases: occlusion, low light, smoke/fog, PPE varieties, posture changes.
- Store data with metadata: site, camera_id, timestamp, environment conditions.
- Maintain a data version tag per collection batch.

Labeling Policy
---------------
- Use a single label taxonomy aligned with `docs/specs/model_class_taxonomy.md`.
- Define class boundaries and ambiguous cases in a shared labeling guide.
- Track labeling quality with random audits and inter-annotator agreement checks.
- Maintain label versioning and change logs.

Train/Validation/Test Split
---------------------------
- Split by camera/time to prevent leakage.
- Keep a fixed, protected test set for final evaluation.
- Record dataset version and split hashes in the training report.

Training Baseline
-----------------
- Start with YOLO baseline (pretrained weights, CPU/GPU as available).
- Use consistent input size and augmentation policy per experiment.
- Track experiments with config snapshots and metrics.

Evaluation Metrics
------------------
- Detection: mAP@0.5, mAP@0.5:0.95, precision, recall.
- Operational: false positives per hour, missed detections per hour.
- Track stability (if tracker enabled): ID switch rate, track fragmentation.

Acceptance Criteria (Draft)
---------------------------
- PERSON detection recall >= 0.90 in validation.
- False positives per hour <= target (to be agreed).
- Latency budget within target FPS (to be agreed).

Deployment/Export
-----------------
- Export to ONNX for runtime use in `ai.vision.adapters.onnx_adapter`.
- Validate model input/output shapes against `docs/specs/model_interface.md`.
- Run a dry-run smoke test in the pipeline with `--visualize`.

Iteration Loop
--------------
- Collect feedback from false positives/negatives.
- Update labels, retrain, and re-run evaluation.
- Update model version and changelog after each iteration.

Risks / Open Questions
----------------------
- Final class taxonomy and severity policy.
- Hardware target and FPS/latency constraints.
- Availability of sufficient labeled data for PPE/POSTURE/SMOKE/FIRE.

Outputs
-------
- Model weights (pt/onnx), versioned.
- Training report (metrics, dataset version, config).
- Deployment checklist and rollback plan.

## 한국어
목적
-----
산업안전 CCTV 파이프라인에 사용할 프로덕션 모델을 만들기 위한 실무형 계획을 정의한다. 데이터 수집, 라벨링, 학습, 평가, 배포 절차의 기준 문서다.

범위
-----
- 필수 클래스(1단계): PERSON, ZONE_INTRUSION, DANGER_ZONE_ENTRY.
- 선택 클래스(2단계 이후): PPE, POSTURE, SMOKE, FIRE, HAZARD.
- v0.2 프로토콜 목록 외 클래스는 프로토콜 업데이트와 정책 확정이 필요하다.

가정
-----
- 하드웨어 타깃은 미정(GPU/Jetson/CPU).
- 해상도/FPS/지연 목표는 미정.
- 예산 목표: 약 100만원(초안).
- 백엔드가 프로토콜 v0.2 페이로드를 수용한다고 가정.

데이터 수집
-----------
- 실제 운영 환경과 유사한 영상 수집(주/야, 실내/실외, 기상 변화 포함).
- 엣지 케이스 포함: 가림, 저조도, 연기/안개, PPE 다양성, 자세 변화.
- 메타데이터 포함 저장: site, camera_id, timestamp, 환경 조건.
- 수집 배치별 데이터 버전 태그 유지.

라벨링 정책
-----------
- `docs/specs/model_class_taxonomy.md`와 동일한 라벨 체계 사용.
- 클래스 경계와 모호 사례를 라벨링 가이드로 명문화.
- 랜덤 감사와 라벨러 간 일치도 점검으로 품질 관리.
- 라벨 변경 기록과 버전 관리 유지.

학습/검증/테스트 분리
---------------------
- 카메라/시간 단위로 분리하여 데이터 누수 방지.
- 고정된 테스트셋을 보호하여 최종 평가에 사용.
- 데이터 버전과 split 해시를 학습 리포트에 기록.

학습 베이스라인
---------------
- YOLO 기준 모델로 시작(사전학습 가중치 사용).
- 입력 해상도와 증강 정책을 실험별로 일관 유지.
- 실험 설정과 지표를 기록한다.

평가 지표
---------
- 탐지 성능: mAP@0.5, mAP@0.5:0.95, precision, recall.
- 운영 지표: 시간당 오탐, 시간당 미탐.
- 트래킹 안정성(트래커 사용 시): ID 스위치율, 트랙 분절.

수용 기준(초안)
--------------
- PERSON 리콜 0.90 이상(검증셋 기준).
- 시간당 오탐 기준 이하(정책 확정 필요).
- 목표 FPS/지연 기준 내(정책 확정 필요).

배포/내보내기
-------------
- 런타임 사용을 위해 ONNX로 내보낸다.
- `docs/specs/model_interface.md`와 입력/출력 형태를 일치시킨다.
- 파이프라인에서 `--visualize`로 스모크 테스트 수행.

반복 개선 루프
-------------
- 오탐/미탐 사례를 수집하고 라벨을 보강.
- 재학습 후 평가 반복.
- 모델 버전과 변경 내역을 기록.

리스크 / 미정 사항
-------------------
- 클래스 분류/심각도 정책 확정.
- 하드웨어 타깃 및 FPS/지연 제약 확정.
- PPE/POSTURE/SMOKE/FIRE 데이터 라벨 규모 확보.

산출물
------
- 모델 가중치(pt/onnx)와 버전.
- 학습 리포트(지표, 데이터 버전, 설정).
- 배포 체크리스트 및 롤백 계획.
