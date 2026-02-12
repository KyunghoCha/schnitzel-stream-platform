# Backend Error Policy - Design

## English
Purpose
-------
- Define how to handle backend failures without stopping pipeline.

Key Decisions
-------------
- Retry with backoff on network/5xx errors.
- Do not retry on 4xx.
- Log failure and continue.

Interfaces
----------
- Inputs:
  - response status
  - exception info
- Outputs:
  - retry decision

Notes
-----
- Cap attempts to prevent infinite loop (unless configured).
- Failure logs include status code and truncated response body.

Code Mapping
------------
- Retry/backoff: `src/ai/clients/backend_api.py`

## 한국어
목적
-----
- 백엔드 실패 시 파이프라인을 멈추지 않고 처리 정책을 정의한다.

핵심 결정
---------
- 네트워크/5xx 오류는 백오프로 재시도한다.
- 4xx는 재시도하지 않는다.
- 실패는 로그로 남기고 계속 진행한다.

인터페이스
----------
- 입력:
  - 응답 상태
  - 예외 정보
- 출력:
  - 재시도 여부

노트
-----
- 무한 루프를 막기 위해 시도 횟수를 제한한다(설정에 따라 예외 가능).
- 실패 로그에 상태 코드와 응답 요약이 포함된다.

코드 매핑
---------
- 재시도/백오프: `src/ai/clients/backend_api.py`
