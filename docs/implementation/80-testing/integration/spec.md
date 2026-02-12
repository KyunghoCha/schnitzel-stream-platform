# Integration Testing - Spec

## English
Behavior
--------
- Run pipeline with sample video.
- Expect JSONL output to contain events.

Config
------
- --output-jsonl and snapshot env vars

Edge Cases
----------
- Backend retry policy is validated by integration tests (backend policy test suite).

Status
------
Implemented in `tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, and `tests/integration/test_zones_api_fallback.py`.

Code Mapping
------------
- Integration tests: `tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, `tests/integration/test_zones_api_fallback.py`

## 한국어
동작
----
- 샘플 영상으로 파이프라인을 실행한다.
- JSONL 출력에 이벤트가 기록되어야 한다.

설정
----
- --output-jsonl 및 스냅샷 환경 변수

엣지 케이스
----------
- 백엔드 재시도 정책은 통합 테스트(backend policy 테스트)에서 검증한다.

상태
----
`tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, `tests/integration/test_zones_api_fallback.py`에 구현됨.

코드 매핑
---------
- 통합 테스트: `tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, `tests/integration/test_zones_api_fallback.py`
