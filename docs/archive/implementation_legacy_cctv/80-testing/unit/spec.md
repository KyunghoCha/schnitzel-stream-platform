# Unit Testing - Spec

## English
Behavior
--------
- Run unit tests with pytest.
- Includes zones cache TTL tests (api/file).
- Includes multi-event builder pipeline test.
- Includes backend retry policy tests (4xx/5xx).
- Includes snapshot save failure test.
- Includes snapshot permission failure test.
- Includes config validation tests.

Config
------
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 (optional)

Status
------
Implemented in `tests/unit/*`.

Code Mapping
------------
- Unit tests: `tests/unit/`

## 한국어
동작
----
- pytest로 유닛 테스트를 실행한다.
- zones 캐시 TTL(api/file) 테스트를 포함한다.
- multi-event builder 파이프라인 테스트를 포함한다.
- backend 재시도 정책(4xx/5xx) 테스트를 포함한다.
- snapshot 저장 실패 테스트를 포함한다.
- snapshot 권한 실패 테스트를 포함한다.
- config 검증 테스트를 포함한다.

설정
----
- PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 (선택)

상태
----
`tests/unit/*`에 구현됨.

코드 매핑
---------
- 유닛 테스트: `tests/unit/`
