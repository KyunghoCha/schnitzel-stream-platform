# Metrics - Spec

## English
Behavior
--------
- Track uptime, fps, frames, drops, accepted events, backend ACK results, errors.
- Also track sensor/fusion counters: `sensor_packets_total`, `sensor_packets_dropped`,
  `sensor_source_errors`, `fusion_attempts`, `fusion_hits`, `fusion_misses`.
- Emit payload to logger at interval.
- `events` / `events_accepted` increment when `emitter.emit()` accepts payload.
- Actual backend delivery results are tracked as `backend_ack_ok` / `backend_ack_fail`.
- `errors` tracks ingest/read failures (not backend POST failures).
- `drops` counts frames skipped by the sampler.

Config
------
- metrics.enabled
- metrics.interval_sec
- metrics.fps_window_sec

Edge Cases
----------
- If disabled, skip metrics.

Status
------
Implemented in `src/ai/utils/metrics.py`.

Code Mapping
------------
- Metrics tracker: `src/ai/utils/metrics.py`
- Metrics logging: `src/ai/pipeline/core.py`

## 한국어
동작
----
- uptime, fps, frames, drops, 수락 이벤트, 백엔드 ACK 결과, errors를 추적한다.
- 센서/융합 카운터(`sensor_packets_total`, `sensor_packets_dropped`,
  `sensor_source_errors`, `fusion_attempts`, `fusion_hits`, `fusion_misses`)도 추적한다.
- 주기적으로 로거에 페이로드를 출력한다.
- `events` / `events_accepted`는 `emitter.emit()` 수락 시 증가한다.
- 실제 백엔드 전달 결과는 `backend_ack_ok` / `backend_ack_fail`로 분리 집계한다.
- `errors`는 ingest/read 실패를 집계하며, backend POST 실패는 포함하지 않는다.
- `drops`는 샘플러에서 건너뛴 프레임 수를 집계한다.

설정
----
- metrics.enabled
- metrics.interval_sec
- metrics.fps_window_sec

엣지 케이스
----------
- 비활성화 시 메트릭을 스킵한다.

상태
----
`src/ai/utils/metrics.py`에 구현됨.

코드 매핑
---------
- 메트릭 추적기: `src/ai/utils/metrics.py`
- 메트릭 로깅: `src/ai/pipeline/core.py`
