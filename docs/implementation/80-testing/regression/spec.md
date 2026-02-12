# Regression Testing - Spec

## English
Behavior
--------
- Run pipeline with fixed input.
- Compare output JSONL to golden JSONL.

Config
------
- tests/regression/golden_events.jsonl

Edge Cases
----------
- If golden file missing, test fails.

Status
------
Implemented in `tests/regression/test_golden.py`.

Code Mapping
------------
- Regression test: `tests/regression/test_golden.py`
- Helper: `scripts/regression_check.py`

## 한국어
동작
----
- 고정 입력으로 파이프라인을 실행한다.
- 출력 JSONL을 골든 JSONL과 비교한다.

설정
----
- tests/regression/golden_events.jsonl

엣지 케이스
----------
- 골든 파일이 없으면 테스트 실패.

상태
----
`tests/regression/test_golden.py`에 구현됨.

코드 매핑
---------
- 회귀 테스트: `tests/regression/test_golden.py`
- 헬퍼: `scripts/regression_check.py`
