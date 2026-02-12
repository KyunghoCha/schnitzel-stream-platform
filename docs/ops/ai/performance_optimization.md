# Performance & Optimization Guide

## English
Purpose
-------
Define a *two-phase* optimization plan: pipeline-level (code/runtime) and model-level.
Real optimization work should be executed **after the final model is selected**.

Phase 0: Baseline (before model finalization)
---------------------------------------------
1. Establish baseline metrics:
   - FPS (avg/95p)
   - Latency per frame
   - CPU/GPU utilization
   - Memory footprint
2. Fix I/O bottlenecks:
   - Ensure RTSP read is stable
   - Avoid unnecessary disk writes
   - Reduce logging verbosity if needed
3. Keep pipeline defaults simple:
   - Use `fps_limit` to cap processing
   - Use `--dry-run` for fast validation

Phase 1: Pipeline Optimization (code/runtime)
---------------------------------------------
- Threading/async handling if bottlenecks are detected.
- Batch inference (if model supports it).
- Frame resize before inference (lower resolution).
- Reduce visualization overhead during production.

Phase 2: Model Optimization (after model fixed)
------------------------------------------------
- ONNX export with static input size.
- Quantization (INT8/FP16) if supported.
- TensorRT engine build (for NVIDIA/Jetson).
- Pruning or smaller architecture if FPS target not met.

Decision Rules
--------------
- If FPS target is missed on CPU, move to GPU/Jetson.
- If GPU still misses target, reduce input resolution or model size.

Status
------
- Guide only. Real optimization is **pending** until model is finalized.

Related Docs
------------
- Model integration: `docs/specs/model_interface.md`
- Runbook: `docs/ops/ops_runbook.md`

## 한국어
목적
-----
최적화를 *2단계*로 정리한다: 파이프라인(코드/런타임)과 모델 최적화.
실제 최적화 작업은 **모델 확정 이후** 수행하는 것이 원칙이다.

Phase 0: 기준선 확보 (모델 확정 전)
-----------------------------------
1. 기준 성능 측정:
   - FPS (평균/95p)
   - 프레임당 지연시간
   - CPU/GPU 사용률
   - 메모리 사용량
2. I/O 병목 제거:
   - RTSP 안정성 확보
   - 불필요한 디스크 쓰기 최소화
   - 필요 시 로그 레벨 축소
3. 기본 파이프라인은 단순 유지:
   - `fps_limit`으로 처리량 제한
   - `--dry-run`으로 빠른 검증

Phase 1: 파이프라인 최적화 (코드/런타임)
-----------------------------------------
- 병목 발견 시 threading/async 적용
- 모델이 지원하면 배치 추론
- 추론 전 해상도 축소
- 운영 환경에서 시각화 비활성화

Phase 2: 모델 최적화 (모델 확정 후)
-----------------------------------
- ONNX export (고정 입력 크기)
- Quantization (INT8/FP16)
- TensorRT 엔진 빌드 (NVIDIA/Jetson)
- FPS 미달 시 경량 모델/프루닝

의사결정 기준
-------------
- CPU에서 FPS 미달 → GPU/Jetson 전환
- GPU에서도 미달 → 해상도/모델 크기 축소

상태
-----
- 가이드 문서이며, 실제 최적화는 모델 확정 이후 진행.

관련 문서
---------
- 모델 연동: `docs/specs/model_interface.md`
- 운영 런북: `docs/ops/ops_runbook.md`
