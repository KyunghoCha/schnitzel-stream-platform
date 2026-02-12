# Unit Testing - Design

## English
Purpose
-------
- Validate small functions in isolation.

Key Decisions
-------------
- Test zone geometry, dedup, config loading, model builders, and snapshots.

Interfaces
----------
- Inputs:
  - function inputs
- Outputs:
  - expected outputs

Notes
-----
- Keep unit tests fast.

Code Mapping
------------
- Unit tests: `tests/unit/`

## 한국어
목적
-----
- 작은 함수 단위로 동작을 검증한다.

핵심 결정
---------
- zone geometry, dedup, config 로딩, model builders, snapshots를 테스트한다.

인터페이스
----------
- 입력:
  - 함수 입력값
- 출력:
  - 기대 출력값

노트
-----
- 유닛 테스트는 빠르게 유지한다.

코드 매핑
---------
- 유닛 테스트: `tests/unit/`
