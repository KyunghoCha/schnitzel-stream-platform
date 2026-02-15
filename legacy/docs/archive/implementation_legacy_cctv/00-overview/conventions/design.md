# Conventions - Design

## English
Purpose
-------
- Keep module boundaries and naming consistent.

Key Decisions
-------------
- Package namespace: `ai.pipeline.*` for pipeline modules.
- Data schemas align to `protocol.md`.
- Config keys follow `configs/*.yaml`.

Interfaces
----------
- Inputs:
  - Configs
  - CLI overrides
- Outputs:
  - Logs and event payloads

Notes
-----
- Prefer dataclasses for config and payloads.

Code Mapping
------------
- Config dataclasses: `src/ai/pipeline/config.py`
- Event schema dataclasses: `src/ai/events/schema.py`

## 한국어
목적
-----
- 모듈 경계와 네이밍을 일관되게 유지한다.

핵심 결정
---------
- 파이프라인 모듈 네임스페이스: `ai.pipeline.*`.
- 데이터 스키마는 `protocol.md`에 맞춘다.
- 설정 키는 `configs/*.yaml` 규칙을 따른다.

인터페이스
----------
- 입력:
  - 설정(Configs)
  - CLI 오버라이드
- 출력:
  - 로그와 이벤트 페이로드

노트
-----
- 설정/페이로드에는 dataclass 사용을 권장한다.

코드 매핑
---------
- 설정 dataclass: `src/ai/pipeline/config.py`
- 이벤트 스키마 dataclass: `src/ai/events/schema.py`
