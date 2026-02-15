# Training Report Template (Draft)

## English
Purpose
-------
Standardize training report contents so experiments are reproducible and comparable.

Metadata
--------
- Model name/version:
- Date:
- Author:
- Dataset version/tag:
- Train/val/test split hash:
- Hardware (GPU/CPU/Jetson):
- Runtime (framework/version):

Training Config
---------------
- Base model weights:
- Input resolution:
- Augmentation policy:
- Epochs:
- Batch size:
- Optimizer / LR schedule:
- Loss functions:

Evaluation Metrics
------------------
- mAP@0.5:
- mAP@0.5:0.95:
- Precision / Recall:
- FPS (inference):
- Latency (p95):
- False positives per hour:
- Missed detections per hour:

Class-wise Results
------------------
- PERSON:
- PPE:
- POSTURE:
- SMOKE:
- FIRE:
- HAZARD:

Operational Notes
-----------------
- Common false positives:
- Common false negatives:
- Failure cases / edge scenarios:
- Model calibration notes:

Artifacts
---------
- Model weights path:
- ONNX export path:
- Example inference outputs:

## 한국어
목적
-----
학습 리포트 내용을 표준화하여 실험 재현성과 비교 가능성을 높인다.

메타데이터
----------
- 모델 이름/버전:
- 날짜:
- 작성자:
- 데이터셋 버전/태그:
- 학습/검증/테스트 split 해시:
- 하드웨어(GPU/CPU/Jetson):
- 런타임(프레임워크/버전):

학습 설정
---------
- 베이스 모델 가중치:
- 입력 해상도:
- 증강 정책:
- 에폭:
- 배치 크기:
- 옵티마이저 / LR 스케줄:
- 손실 함수:

평가 지표
---------
- mAP@0.5:
- mAP@0.5:0.95:
- Precision / Recall:
- FPS(추론):
- 지연(p95):
- 시간당 오탐:
- 시간당 미탐:

클래스별 결과
-------------
- PERSON:
- PPE:
- POSTURE:
- SMOKE:
- FIRE:
- HAZARD:

운영 메모
---------
- 자주 발생하는 오탐:
- 자주 발생하는 미탐:
- 실패 케이스 / 엣지 시나리오:
- 모델 보정 관련 메모:

산출물
------
- 모델 가중치 경로:
- ONNX 변환 경로:
- 예시 추론 결과:
