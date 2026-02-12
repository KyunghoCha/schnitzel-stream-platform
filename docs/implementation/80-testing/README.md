# Testing

## English
Status
------
Unit, integration, and regression tests are implemented under `tests/`.
Snapshot failure cases are covered by unit tests.
Static hygiene checks are available via `scripts/test_hygiene.py`.

Notes
-----
Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` if external pytest plugins cause issues.
CI includes a hygiene ratchet gate (`.github/workflows/ci.yml`) to prevent worsening duplicate/no-assert counts.

Code Mapping
------------
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Regression tests: `tests/regression/`
- Regression helper: `scripts/regression_check.py`
- Test hygiene checker: `scripts/test_hygiene.py`

## 한국어
상태
----
`tests/` 아래에 unit/integration/regression 테스트가 구현되어 있음.
스냅샷 실패 케이스는 유닛 테스트로 검증됨.
정적 테스트 위생 점검은 `scripts/test_hygiene.py`로 수행 가능.

노트
----
외부 pytest 플러그인 문제 시 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 사용.
CI에는 테스트 위생 래칫 게이트(`.github/workflows/ci.yml`)가 포함되어 중복/무검증 수치 악화를 차단함.

코드 매핑
---------
- 유닛 테스트: `tests/unit/`
- 통합 테스트: `tests/integration/`
- 회귀 테스트: `tests/regression/`
- 회귀 헬퍼: `scripts/regression_check.py`
- 테스트 위생 점검 도구: `scripts/test_hygiene.py`
