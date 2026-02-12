# Integration Testing - Design

## English
Purpose
-------
- Validate pipeline wiring end-to-end.

Key Decisions
-------------
- Use JSONL output for integration validation.
- Test snapshot writing to temp directory.

Interfaces
----------
- Inputs:
  - pipeline CLI
- Outputs:
  - JSONL output file
  - snapshot files (optional)

Notes
-----
- Keep tests deterministic with sample video.

Code Mapping
------------
- Integration tests: `tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, `tests/integration/test_zones_api_fallback.py`

## 한국어
목적
-----
- 파이프라인 결합을 end-to-end로 검증한다.

핵심 결정
---------
- JSONL 출력으로 통합 동작을 검증한다.
- 스냅샷 저장은 임시 디렉터리에 기록한다.

인터페이스
----------
- 입력:
  - 파이프라인 CLI
- 출력:
  - JSONL 출력 파일
  - 스냅샷 파일(옵션)

노트
-----
- 샘플 영상으로 테스트를 결정적으로 유지한다.

코드 매핑
---------
- 통합 테스트: `tests/integration/test_pipeline_jsonl.py`, `tests/integration/test_backend_policy.py`, `tests/integration/test_zones_api_fallback.py`
