# Regression Testing - Design

## English
Purpose
-------
- Detect behavior drift using golden event outputs.

Key Decisions
-------------
- Store golden events in JSONL.
- Compare new run output to golden file.

Interfaces
----------
- Inputs:
  - golden file
  - current output
- Outputs:
  - diff/FAIL

Notes
-----
- Keep golden data small and deterministic.

Code Mapping
------------
- Regression tests: `tests/regression/test_golden.py`
- Helper: `scripts/regression_check.py`

## 한국어
목적
-----
- 골든 이벤트 출력으로 동작 드리프트를 감지한다.

핵심 결정
---------
- 골든 이벤트를 JSONL로 저장한다.
- 현재 실행 결과를 골든 파일과 비교한다.

인터페이스
----------
- 입력:
  - 골든 파일
  - 현재 출력
- 출력:
  - diff/FAIL

노트
-----
- 골든 데이터는 작고 결정적으로 유지한다.

코드 매핑
---------
- 회귀 테스트: `tests/regression/test_golden.py`
- 헬퍼: `scripts/regression_check.py`
