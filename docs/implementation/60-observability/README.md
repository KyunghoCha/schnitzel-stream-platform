# Observability

## English
Status
------
Implemented in `src/ai/utils/metrics.py` and `src/ai/logging_setup.py`.

Logging Notes
-------------
- Logs are written to file and stdout.
- Log filename includes camera_id to avoid collisions in multi-process runs.
- The camera_id suffix is sanitized for safe filenames.
- File logging uses rotation (size-based). Control via:
  - `AI_LOG_MAX_BYTES` (default 10MB)
  - `AI_LOG_BACKUP_COUNT` (default 5)
- RTSP URLs and backend post_url in startup logs are masked (password hidden).
- Log level/format can be overridden:
  - `AI_LOG_LEVEL` (default `INFO`)
  - `AI_LOG_FORMAT` (default `plain`, or `json`)
- Config-level overrides:
  - `AI_LOGGING_LEVEL`
  - `AI_LOGGING_FORMAT`
- Structured fields are included when available:
  - `camera_id`, `event_id`, `event_type`
  - `error_code` (ex: `RTSP_READ_FAILED`, `BACKEND_POST_FAILED`)
- Metrics/heartbeat are logged by dedicated loggers:
  - `ai.metrics` with `metrics` field
  - `ai.heartbeat` with `heartbeat` field

Error Codes
-----------
- `RTSP_READ_FAILED`: retrying after RTSP read failure
- `BACKEND_POST_FAILED`: POST failed (will retry)
- `BACKEND_NON_2XX`: backend returned non-2xx
- `BACKEND_POST_GIVEUP`: POST failed after all retries

Code Mapping
------------
- Logging setup: `src/ai/logging_setup.py`
- Metrics/heartbeat: `src/ai/utils/metrics.py`, `src/ai/pipeline/core.py`

Log Samples (JSON)
------------------
```json
{"ts":"2026-02-04T19:10:00","level":"INFO","logger":"ai.pipeline.core","message":"emit_ok=True event_id=... frame=10","camera_id":"cam01","source_type":"rtsp","event_id":"...","event_type":"ZONE_INTRUSION","error_code":"-"}
{"ts":"2026-02-04T19:10:05","level":"WARNING","logger":"ai.pipeline.core","message":"frame_read_failed retrying in 1.03s (failures=2)","camera_id":"cam01","source_type":"RtspSource","error_code":"RTSP_READ_FAILED"}
{"ts":"2026-02-04T19:10:10","level":"INFO","logger":"ai.metrics","message":"metrics","camera_id":"cam01","metrics":{"uptime_sec":10.0,"fps":9.8,"frames":98,"drops":0,"events":9,"errors":1}}
```

## 한국어
상태
----
`src/ai/utils/metrics.py`와 `src/ai/logging_setup.py`에 구현됨.

로깅 노트
----------
- 로그는 파일과 stdout에 기록된다.
- 멀티프로세스 실행 시 충돌 방지를 위해 로그 파일명에 camera_id가 포함된다.
- camera_id suffix는 안전한 파일명으로 정규화된다.
- 파일 로깅은 회전(크기 기준)으로 관리한다.
  - `AI_LOG_MAX_BYTES` (기본 10MB)
  - `AI_LOG_BACKUP_COUNT` (기본 5)
- 시작 로그의 RTSP URL과 backend post_url은 마스킹(비밀번호 숨김)된다.
- 로그 레벨/포맷은 다음으로 오버라이드 가능:
  - `AI_LOG_LEVEL` (기본 `INFO`)
  - `AI_LOG_FORMAT` (기본 `plain`, 또는 `json`)
- 설정 레벨 오버라이드:
  - `AI_LOGGING_LEVEL`
  - `AI_LOGGING_FORMAT`
- 구조화 필드는 가능할 때 포함된다:
  - `camera_id`, `event_id`, `event_type`
  - `error_code` (예: `RTSP_READ_FAILED`, `BACKEND_POST_FAILED`)
- Metrics/heartbeat는 전용 로거로 기록된다:
  - `ai.metrics`는 `metrics` 필드 포함
  - `ai.heartbeat`는 `heartbeat` 필드 포함

에러 코드
----------
- `RTSP_READ_FAILED`: RTSP read 실패 후 재시도 중
- `BACKEND_POST_FAILED`: POST 실패(재시도 예정)
- `BACKEND_NON_2XX`: 백엔드 응답이 2xx가 아님
- `BACKEND_POST_GIVEUP`: 재시도 후에도 POST 실패

코드 매핑
---------
- 로깅 설정: `src/ai/logging_setup.py`
- 메트릭/하트비트: `src/ai/utils/metrics.py`, `src/ai/pipeline/core.py`

로그 샘플(JSON)
---------------
```json
{"ts":"2026-02-04T19:10:00","level":"INFO","logger":"ai.pipeline.core","message":"emit_ok=True event_id=... frame=10","camera_id":"cam01","source_type":"rtsp","event_id":"...","event_type":"ZONE_INTRUSION","error_code":"-"}
{"ts":"2026-02-04T19:10:05","level":"WARNING","logger":"ai.pipeline.core","message":"frame_read_failed retrying in 1.03s (failures=2)","camera_id":"cam01","source_type":"RtspSource","error_code":"RTSP_READ_FAILED"}
{"ts":"2026-02-04T19:10:10","level":"INFO","logger":"ai.metrics","message":"metrics","camera_id":"cam01","metrics":{"uptime_sec":10.0,"fps":9.8,"frames":98,"drops":0,"events":9,"errors":1}}
```
