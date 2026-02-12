# Backend Client - Design

## English
Purpose
-------
- POST events to backend reliably.

Key Decisions
-------------
- Use `urllib` with timeout and retry.
- Treat non-2xx as failure.
- Do not retry on 4xx.

Interfaces
----------
- Inputs:
  - post_url
  - payload
  - timeout
  - retry policy
- Outputs:
  - ok boolean and error info

Notes
-----
- Keep HTTP client small and testable.

Code Mapping
------------
- Backend client: `src/ai/clients/backend_api.py`

## 한국어
목적
-----
- 이벤트를 백엔드로 안정적으로 POST한다.

핵심 결정
---------
- timeout과 재시도를 가진 `urllib`을 사용한다.
- non-2xx 응답은 실패로 처리한다.
- 4xx에는 재시도하지 않는다.

인터페이스
----------
- 입력:
  - post_url
  - payload
  - timeout
  - 재시도 정책
- 출력:
  - ok 여부 및 에러 정보

노트
-----
- HTTP 클라이언트를 작고 테스트 가능하게 유지한다.

코드 매핑
---------
- 백엔드 클라이언트: `src/ai/clients/backend_api.py`
