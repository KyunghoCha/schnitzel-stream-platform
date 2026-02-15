# Schema Validation - Spec

## English
Behavior
--------
- Validate config on load.
- Raise error if required fields missing.

Edge Cases
----------
- Optional fields may be omitted.

Status
------
Implemented in `src/ai/config.py`.

Code Mapping
------------
- Validation: `src/ai/config.py` (`validate_config`)

## 한국어
동작
----
- 로드 시 설정을 검증한다.
- 필수 필드 누락 시 에러를 발생시킨다.

엣지 케이스
----------
- optional 필드는 생략 가능하다.

상태
----
`src/ai/config.py`에 구현됨.

코드 매핑
---------
- 검증: `src/ai/config.py` (`validate_config`)
