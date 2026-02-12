# RTSP Health Metrics - Spec

## English
Behavior
--------
- Collect fps, frames, drops, errors per camera.
- Emit metrics periodically via logger.

Config
------
- metrics.enabled
- metrics.interval_sec
- metrics.fps_window_sec

Edge Cases
----------
- If metrics disabled, collector is a no-op.
- Missing camera_id should not crash metrics logging.

Status
------
Implemented in `src/ai/utils/metrics.py` and `src/ai/pipeline/core.py`.

Code Mapping
------------
- Metrics tracker: `src/ai/utils/metrics.py`
- Metrics log hooks: `src/ai/pipeline/core.py`

## 한국어
동작
----
- 카메라별 fps, frames, drops, errors를 수집한다.
- 전용 로거로 주기적으로 메트릭을 출력한다.

설정
----
- metrics.enabled
- metrics.interval_sec
- metrics.fps_window_sec

엣지 케이스
----------
- metrics가 비활성화되면 수집기는 no-op이다.
- camera_id가 없더라도 메트릭 로그가 크래시되면 안 된다.

상태
----
`src/ai/utils/metrics.py` 및 `src/ai/pipeline/core.py`에 구현됨.

코드 매핑
---------
- 메트릭 추적기: `src/ai/utils/metrics.py`
- 메트릭 로깅 훅: `src/ai/pipeline/core.py`
