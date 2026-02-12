# RTSP Timeout Watchdog - Spec

## English

Behavior
--------

- If now - last_frame_ts > timeout_sec, trigger reconnect inside the RTSP source.

Config
------

- timeout_sec (default: 5.0)

Edge Cases
----------

- Pause during reconnect should reset last_frame_ts.
- Very low FPS streams need higher timeout_sec.

Status
------

Implemented in `src/ai/pipeline/sources.py` (timeout check uses `last_frame_ts`).

Code Mapping
------------

- Timeout check: `src/ai/pipeline/sources/rtsp.py` (`RtspSource.read`)

## 한국어

동작
----

- now - last_frame_ts > timeout_sec 이면 RTSP 소스 내부에서 재연결을 트리거한다.

설정
----

- timeout_sec (기본값: 5.0)

엣지 케이스
----------

- 재연결 중의 일시 정지는 last_frame_ts를 초기화해야 한다.
- 매우 낮은 FPS 스트림은 더 큰 timeout_sec가 필요하다.

상태
----

`src/ai/pipeline/sources.py`에 구현됨(타임아웃 체크는 `last_frame_ts` 사용).

코드 매핑
---------

- 타임아웃 체크: `src/ai/pipeline/sources/rtsp.py` (`RtspSource.read`)
