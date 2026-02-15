# Heartbeat - Design

## English
Purpose
-------
- Emit periodic heartbeat logs for liveness.

Key Decisions
-------------
- Heartbeat is a lightweight log event.
- Use dedicated logger (`ai.heartbeat`).

Interfaces
----------
- Inputs:
  - interval_sec
- Outputs:
  - heartbeat payload
  - last_frame_age_sec (seconds since last frame, when available)

Notes
-----
- Should not block pipeline.

Code Mapping
------------
- Heartbeat tracker: `src/ai/utils/metrics.py` (`Heartbeat`)

## 한국어
목적
-----
- 생존 확인을 위한 주기적 하트비트 로그를 발행한다.

핵심 결정
---------
- 하트비트는 가벼운 로그 이벤트로 처리한다.
- 전용 로거(`ai.heartbeat`)를 사용한다.

인터페이스
----------
- 입력:
  - interval_sec
- 출력:
  - 하트비트 페이로드
  - last_frame_age_sec (마지막 프레임 경과 시간, 가능할 때)

노트
-----
- 파이프라인을 블로킹하지 않아야 한다.

코드 매핑
---------
- 하트비트 추적기: `src/ai/utils/metrics.py` (`Heartbeat`)
