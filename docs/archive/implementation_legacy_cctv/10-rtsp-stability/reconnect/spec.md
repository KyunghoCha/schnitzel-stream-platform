# RTSP Reconnect - Spec

## English

Behavior
--------

- On read failure, retry without tearing down the pipeline.
- On open failure, reinitialize the RTSP source.
- Use exponential backoff with jitter between attempts.
- If max_attempts is 0, retry forever.
- If max_attempts is set and exceeded, reconnect is disabled and the pipeline exits.
- After a successful reconnect, the next pipeline loop skips the long backoff and only applies a short minimal delay.

Config
------

- base_delay_sec
- max_delay_sec
- max_attempts
- jitter_ratio

Edge Cases
----------

- Some streams never send EOF; treat long silence as timeout.
- Credentials changes require a fresh connection.

Status
------

Implemented in `src/ai/pipeline/sources/rtsp.py` (RtspSource reconnect loop).

Code Mapping
------------

- RTSP reconnect loop: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)

## 한국어

동작
----

- read 실패 시 파이프라인을 유지한 채 재시도한다.
- open 실패 시 RTSP 소스를 재초기화한다.
- 시도 간 지수 백오프 + 지터를 사용한다.
- max_attempts가 0이면 무한 재시도한다.
- max_attempts를 설정했는데 초과하면 재연결을 중단하고 파이프라인이 종료된다.
- 재연결 성공 직후에는 긴 backoff는 건너뛰고 짧은 최소 지연만 적용한다.

설정
----

- base_delay_sec
- max_delay_sec
- max_attempts
- jitter_ratio

엣지 케이스
----------

- 일부 스트림은 EOF를 보내지 않으므로 긴 무응답을 타임아웃으로 처리한다.
- 인증 정보가 바뀌면 새 연결이 필요하다.

상태
----

`src/ai/pipeline/sources/rtsp.py`에 구현됨(RtspSource 재연결 루프).

코드 매핑
---------

- RTSP 재연결 루프: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)
