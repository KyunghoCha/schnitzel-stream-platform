# Backend Error Policy - Spec

## English
Behavior
--------
- If POST fails, retry per policy.
- If retries exhausted, give up and log.

Config
------
- events.retry.max_attempts
- failures are logged with status/response summary
- backend failures retry by policy; pipeline keeps running
- events.retry.backoff_sec

Edge Cases
----------
- Backend returns 4xx -> no retry.

Status
------
Implemented in `src/ai/clients/backend_api.py`.
Integration tests live in `tests/integration/test_backend_policy.py`.

Code Mapping
------------
- Retry/backoff: `src/ai/clients/backend_api.py`

## 한국어
동작
----
- POST 실패 시 정책에 따라 재시도한다.
- 재시도 횟수를 소진하면 포기하고 로그를 남긴다.

설정
----
- events.retry.max_attempts
- 실패 시 상태/응답 요약이 로그로 남는다
- 백엔드 실패는 정책에 따라 재시도하며 파이프라인은 유지된다
- events.retry.backoff_sec

엣지 케이스
----------
- 백엔드가 4xx를 반환하면 재시도하지 않는다.

상태
----
`src/ai/clients/backend_api.py`에 구현됨.
통합 테스트는 `tests/integration/test_backend_policy.py`.

코드 매핑
---------
- 재시도/백오프: `src/ai/clients/backend_api.py`
