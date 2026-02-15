# Architecture - Design

## English
Purpose
-------
- Define the non-model system architecture and module boundaries.
- Ensure each module is replaceable without breaking the pipeline.

Key Decisions
-------------
- Pipeline is composed of pluggable modules: Source, Sampler, EventBuilder, Emitter.
- All runtime behavior is driven by config + small CLI overrides.
- Keep IO at the edges (source/emitter); core stays pure.

Interfaces
----------
- Inputs:
  - Video frames from Source
  - Config (ingest/events/zones/etc.)
- Outputs:
  - Event payloads (protocol.md aligned)

Notes
-----
- Model inference details are excluded from this architecture scope.
- `ingest/` is reserved for future expansion.

Code Mapping
------------
- Pipeline core: `src/ai/pipeline/core.py`
- Phase 0 wiring: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`

## 한국어
목적
-----
- 모델 제외 시스템 아키텍처와 모듈 경계를 정의한다.
- 각 모듈을 교체해도 파이프라인이 깨지지 않게 한다.

핵심 결정
---------
- 파이프라인은 플러그형 모듈로 구성: Source, Sampler, EventBuilder, Emitter.
- 런타임 동작은 설정 + 최소한의 CLI 오버라이드로 제어한다.
- IO는 경계(source/emitter)에 두고, 코어는 순수하게 유지한다.

인터페이스
----------
- 입력:
  - Source에서 들어오는 비디오 프레임
  - 설정(ingest/events/zones 등)
- 출력:
  - 이벤트 페이로드(`protocol.md` 기준)

노트
-----
- 이 범위에는 모델 추론의 세부 구현이 포함되지 않는다.
- `ingest/`는 향후 확장을 위해 비워둔 영역이다.

코드 매핑
---------
- 파이프라인 코어: `src/ai/pipeline/core.py`
- Phase 0 연결: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
