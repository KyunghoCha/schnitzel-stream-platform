# RTSP Timeout Watchdog - Design

## English

Purpose
-------

- Detect stalled RTSP streams and trigger reconnect.

Key Decisions
-------------

- Track `last_frame_ts` per source.
- Declare timeout when `now - last_frame_ts` exceeds threshold.

Interfaces
----------

- Inputs:
  - frame timestamps
  - timeout_sec
- Outputs:
  - timeout signal to reconnect controller

Notes
-----

- Should be robust to very low FPS streams.

Code Mapping
------------

- Timeout detection is embedded in `src/ai/pipeline/sources/rtsp.py` (`RtspSource.read`)

## 한국어

목적
-----

- RTSP 스트림 정지 상태를 감지하고 재연결을 트리거한다.

핵심 결정
---------

- 소스별로 `last_frame_ts`를 추적한다.
- `now - last_frame_ts`가 임계값을 넘으면 타임아웃으로 판단한다.

인터페이스
----------

- 입력:
  - 프레임 타임스탬프
  - timeout_sec
- 출력:
  - 재연결 컨트롤러로 타임아웃 신호 전달

노트
-----

- 매우 낮은 FPS 스트림에도 견고해야 한다.

코드 매핑
---------

- 타임아웃 감지는 `src/ai/pipeline/sources/rtsp.py` (`RtspSource.read`)에 내장됨
