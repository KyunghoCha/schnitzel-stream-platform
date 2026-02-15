# Backend Client - Spec

## English
Behavior
--------
- POST payload to post_url with timeout.
- Log status code and truncated response body on failures.
- Retry on network errors and 5xx.
- Do not retry on 4xx.

Config
------
- events.post_url
- events.timeout_sec
- events.retry.max_attempts
- events.retry.backoff_sec

Edge Cases
----------
- If host is not resolvable, pipeline falls back to stdout (dry-run).

Status
------
Implemented in `src/ai/clients/backend_api.py`.

Code Mapping
------------
- Backend client: `src/ai/clients/backend_api.py`

## 한국어
동작
----
- post_url로 payload를 timeout과 함께 POST한다.
- 실패 시 상태 코드와 응답 요약(일부)을 로그로 남긴다.
- 네트워크 오류와 5xx는 재시도한다.
- 4xx는 재시도하지 않는다.

설정
----
- events.post_url
- events.timeout_sec
- events.retry.max_attempts
- events.retry.backoff_sec

엣지 케이스
----------
- 호스트를 해석할 수 없으면 파이프라인에서 stdout(dry-run)으로 폴백한다.

상태
----
`src/ai/clients/backend_api.py`에 구현됨.

코드 매핑
---------
- 백엔드 클라이언트: `src/ai/clients/backend_api.py`
