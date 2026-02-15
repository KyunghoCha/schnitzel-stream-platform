# RTSP Reconnect - Design

## English

Purpose
-------

- Keep the pipeline alive when RTSP drops or stalls.
- Minimize downtime and avoid tight reconnect loops.

Key Decisions
-------------

- Use a reconnect controller with exponential backoff and jitter.
- Reset the VideoCapture instance on reconnect.
- Separate "soft" retry (read failure) vs "hard" retry (open failure).
- Skip the long backoff right after a successful reconnect, but keep a short minimal delay.

Interfaces
----------

- Inputs:
  - source_url
  - retry policy (base_delay, max_delay, max_attempts, jitter)
  - failure signals (read timeout, open failure)
- Outputs:
  - new source instance or fatal error after max attempts

Notes
-----

- Prefer short sleep in reconnect loop to avoid CPU spin.
- Log reason and attempt counts for observability.
- If max_attempts is exceeded, disable reconnect and exit the pipeline.

Code Mapping
------------

- RTSP reconnect loop: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)

## 한국어

목적
-----

- RTSP 끊김/정지 시 파이프라인을 유지한다.
- 다운타임을 최소화하고 과도한 재연결 루프를 피한다.

핵심 결정
---------

- 지수 백오프 + 지터가 있는 재연결 컨트롤러를 사용한다.
- 재연결 시 VideoCapture 인스턴스를 재생성한다.
- "소프트" 재시도(읽기 실패)와 "하드" 재시도(오픈 실패)를 분리한다.
- 재연결 성공 직후에는 긴 backoff는 건너뛰되 짧은 최소 지연은 유지한다.

인터페이스
----------

- 입력:
  - source_url
  - 재시도 정책(base_delay, max_delay, max_attempts, jitter)
  - 실패 신호(read timeout, open failure)
- 출력:
  - 새로운 소스 인스턴스 또는 최대 시도 이후 치명 오류

노트
-----

- 재연결 루프에서는 짧게 sleep하여 CPU 스핀을 방지한다.
- 원인과 시도 횟수를 로그로 남겨 가시성을 확보한다.
- max_attempts를 초과하면 재연결을 중단하고 파이프라인을 종료한다.

코드 매핑
---------

- RTSP 재연결 루프: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)
