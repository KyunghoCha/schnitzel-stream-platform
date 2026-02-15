# Schema Validation - Design

## English
Purpose
-------
- Validate configs against schema to catch errors early.

Key Decisions
-------------
- Validate required sections and basic field types.
- Use lightweight checks (no formal schema enforcement).

Interfaces
----------
- Inputs:
  - config dict
- Outputs:
  - validated config or error

Notes
-----
- Keep schema aligned with `configs/*.yaml`.

Code Mapping
------------
- Validation: `src/ai/config.py` (`validate_config`)

## 한국어
목적
-----
- 설정을 스키마로 검증하여 오류를 조기에 발견한다.

핵심 결정
---------
- 별도 스키마 없이 기본 필드/타입만 검증한다.
- 유효하지 않으면 빠르게 실패한다.

인터페이스
----------
- 입력:
  - config dict
- 출력:
  - 검증된 설정 또는 에러

노트
-----
- 스키마는 `configs/*.yaml`와 정렬한다.

코드 매핑
---------
- 검증: `src/ai/config.py` (`validate_config`)
