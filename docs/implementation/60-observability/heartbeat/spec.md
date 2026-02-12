# Heartbeat - Spec

## English
Behavior
--------
- Emit heartbeat log at fixed interval.
- Include camera_id when available.
- Payload includes `last_frame_age_sec` (seconds since last frame).

Config
------
- heartbeat.enabled
- heartbeat.interval_sec

Edge Cases
----------
- If disabled, no heartbeat logs.

Status
------
Implemented in `src/ai/pipeline/core.py`.

Code Mapping
------------
- Heartbeat tracker: `src/ai/utils/metrics.py`
- Heartbeat logging: `src/ai/pipeline/core.py`

## 한국어
동작
----
- 고정 주기로 하트비트 로그를 출력한다.
- 가능하면 camera_id를 포함한다.
- 페이로드에 마지막 프레임 경과 시간 `last_frame_age_sec`를 포함한다.

설정
----
- heartbeat.enabled
- heartbeat.interval_sec

엣지 케이스
----------
- 비활성화 시 하트비트 로그 없음.

상태
----
`src/ai/pipeline/core.py`에 구현됨.

코드 매핑
---------
- 하트비트 추적기: `src/ai/utils/metrics.py`
- 하트비트 로깅: `src/ai/pipeline/core.py`
