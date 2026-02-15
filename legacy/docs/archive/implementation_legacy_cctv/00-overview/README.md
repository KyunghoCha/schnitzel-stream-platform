# Overview

## English

## Scope

- Pipeline readiness (non-model + model adapter integration)
- Model training is excluded (inference adapters only)

## Status

Implemented as of 2026-02-09. Remaining gaps are tracked in `docs/roadmap/execution_roadmap.md`.

## Code Mapping

- Entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Phase 0 wiring: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- Legacy core: `src/ai/pipeline/core.py`

## 한국어

## 범위

- 파이프라인 준비 상태(비모델 + 모델 어댑터 연동) 포함
- 모델 학습은 제외(추론 어댑터만 포함)

## 상태

2026-02-09 기준 구현 완료. 남은 항목은 `docs/roadmap/execution_roadmap.md`에서 추적.

## 코드 매핑

- 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- Phase 0 연결: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 레거시 코어: `src/ai/pipeline/core.py`
