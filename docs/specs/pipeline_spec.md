# pipeline_spec

## English

Pipeline Spec
=============

## Entrypoint

- Entrypoint module: `schnitzel_stream` (package)
- Legacy runtime package: `ai.pipeline` (executed via Phase 0 job indirection)
- Windows (Recommended): `./setup_env.ps1; python -m schnitzel_stream`
- Linux/Manual: `PYTHONPATH=src python -m schnitzel_stream`

## Inputs

- **Video**: `data/samples/*.mp4` (default)
- **CLI Overrides**:
  - `--graph` (graph spec YAML path; default: `configs/graphs/legacy_pipeline.yaml`; v2 graphs require `--validate-only` until Phase 1 runtime ships)
  - `--video` (mp4 path; forces file source, fails fast if path does not exist)
  - `--camera-id` (string; fails fast if id is not found in `configs/cameras.yaml`)
  - `--source-type` (file|rtsp|webcam|plugin; `--video` + `--source-type rtsp/plugin` is invalid)
  - `--camera-index` (int; webcam device index override, default uses `cameras.yaml` `source.index` or 0)
  - `--validate-only` (validate the graph spec and exit without running)
  - `--dry-run` (no backend posts)
  - `--output-jsonl` (write events to file)
  - `--max-events` (limit emitting)
  - `--visualize` (show debug window)
  - `--loop` (loop video file indefinitely; only for file sources)

## Config (loaded from `configs/default.yaml` + `configs/cameras.yaml`)

- Optional runtime profile overlay: `configs/dev.yaml` or `configs/prod.yaml` based on `app.env`
- `app.site_id` -> event site_id
- `app.timezone` -> event ts timezone
- `ingest.fps_limit` -> downsample FPS
- `source.adapter` -> optional input source plugin (`module:ClassName`, for `source.type=plugin`)
- `sensor.*` -> multimodal sensor lane config (`enabled`, `type`, `adapter`, `topic`, `queue_size`, `time_window_ms`, `emit_events`, `emit_fused_events`)
  - P2 baseline behavior:
    - nearest sensor packet attachment into each vision event (`sensor`)
    - optional independent `SENSOR_EVENT` emission (`sensor.emit_events=true`)
    - optional `FUSED_EVENT` emission (`sensor.emit_fused_events=true`)
- `events.post_url` -> backend endpoint
- `events.timeout_sec` -> request timeout
- `events.emitter_adapter` -> optional custom output emitter (`module:ClassName`)
- `events.retry.max_attempts` / `events.retry.backoff_sec`
- `events.snapshot.base_dir` / `events.snapshot.public_prefix`
- Snapshots are disabled by default; enable by setting `events.snapshot.base_dir`.
- Multi-camera configs can live in `configs/cameras.yaml` under `cameras:`.
- Webcam source can set `source.index` in `configs/cameras.yaml`.
- Config file relative paths (e.g., file source path, zones file path) are resolved against repo root.
- `zones.*` and `rules.rule_point_by_event_type` control zone loading and inside evaluation.

## Output Payload (dummy, aligned to protocol.md)

- `event_id` (uuid string)
- `ts` (ISO-8601, uses app.timezone when set)
- `site_id` (string)
- `camera_id` (string)
- `event_type` = vision type (e.g., "ZONE_INTRUSION"), optional sensor extensions: `SENSOR_EVENT`, `FUSED_EVENT`
- `object_type` = "PERSON"
- `severity` = "LOW"
- `track_id` (int or null; required for PERSON)
- `bbox` = `{x1,y1,x2,y2}`
- `confidence` = 0.75 (MockModelEventBuilder)
- `zone` = `{zone_id, inside}`
- `snapshot_path` = string when snapshot is enabled **and saved**, otherwise null
- `sensor` = optional object (nearest packet within `sensor.time_window_ms`), otherwise null

## Multi-Event Support

- Builder returns a list of payload dicts (`0..N` events per frame).
- The pipeline emits each payload in list order.

## Model Integration (real-first)

- `configs/default.yaml` -> `model.mode`
  - `real` (default): requires `model.adapter` / `AI_MODEL_ADAPTER`; startup fails if missing
    - default `CustomModelAdapter` is a template and fails fast until implemented
  - `mock`: test-only mode, must be enabled explicitly (e.g., `AI_MODEL_MODE=mock`)
  - other values: fail-fast with startup error
- Model/Tracker outputs must map to the same payload keys:
  - `bbox`, `confidence`, `track_id` (required for PERSON; synthetic if no tracker),
    `event_type`, `object_type`, `severity`

## Behavior

- Uses OpenCV to read frames
- Samples frames based on FPS limit
- Sampling uses a rate-based selector to avoid overshooting target FPS
- Mock builder (explicit `model.mode=mock`) emits one dummy event per processed frame when dedup is disabled
- Real builder may return 0..N events per frame (list)
- If `source.type=plugin`, input source is loaded via `source.adapter` / `AI_SOURCE_ADAPTER`
- If `sensor.enabled=true`, sensor plugin is loaded via `sensor.adapter` / `AI_SENSOR_ADAPTER` (single) or `sensor.adapters` / `AI_SENSOR_ADAPTERS` (multi)
- Sensor lane attaches nearest packet to each event (`payload.sensor`) using `sensor.time_window_ms`
- If `sensor.emit_events=true`, sensor lane also emits independent `SENSOR_EVENT` payloads
- If `sensor.emit_fused_events=true`, fusion wrapper emits additional `FUSED_EVENT` payloads
- Final hazard/alarm decision is out of runtime scope by default: runtime emits evidence events, and user policy decides final action (backend policy layer is optional). If required by deployment policy, runtime may be extended to make final decisions via in-runtime rule/plugin stage.
- If `events.emitter_adapter` is configured, a custom emitter plugin is loaded
- Built-in ROS2 plugin templates are available:
  - source: `ai.plugins.ros2.image_source:Ros2ImageSource`
  - emitter: `ai.plugins.ros2.event_emitter:Ros2EventEmitter`
  - requires ROS2 Python packages (`rclpy`, `sensor_msgs`, `std_msgs`)
- Built-in no-hardware sensor template:
  - sensor adapter: `ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource`
- If backend host is not resolvable, it falls back to stdout (dry-run)
- **Backend Retry Policy**: HTTP 4xx responses are dropped without retry (client error); only 5xx or network errors trigger retry with exponential backoff.
- Invalid camera id fails fast at startup
- Invalid timezone falls back to UTC
- For RTSP sources, read failures trigger retry with backoff+jitter
  - If `rtsp.max_attempts` is set and exceeded, the source disables reconnect and the pipeline stops.
- After a successful RTSP reconnect, the pipeline applies a short 0.2s delay to avoid a tight loop.
- **RTSP Transport**: Defaults to `tcp` to prevent packet loss and image corruption (smearing) on high-resolution streams. Can be overridden to `udp` via `AI_RTSP_TRANSPORT` env var if latency is critical.
- **FPS Throttling**: For file sources, the pipeline core throttles playback to match the source FPS, ensuring real-time playback speed.
- **Smooth Visualization**: When `--visualize` is enabled, every frame is displayed (not just sampled frames). Detection boxes from the last analysis are retained to prevent flickering. To prevent "buffer staining" caused by OpenCV memory reuse, the visualizer works on a copy of the frame. Each camera uses a unique window name (`AI Pipeline - <camera_id>`) to support multi-camera monitoring.
- **Threaded Frame Reader**: Live sources (`is_live=True`) are automatically wrapped with `ThreadedSource`, which reads frames in a background thread. This prevents frame drops and decoder corruption caused by model inference blocking `source.read()`.
- **Async Frame Processing (Display-First)**: For live sources (`is_live=True`), `FrameProcessor` runs inference in a background worker thread. The worker updates display results immediately after inference, *before* zone evaluation and emission. This prevents display stutter caused by zone API fetch latency. File sources (`is_live=False`) use synchronous processing to preserve frame ordering.
- **Non-blocking Zone API Refresh**: When `zones.source=api`, zone fetch is refreshed asynchronously. Event processing uses cache first (including stale cache fallback) so temporary zone API outages do not directly block inference paths.
- `AI_ZONES_SOURCE` can override `zones.source` at runtime (`file`, `api`, or `none`).
  - `none` disables zone evaluation (`payload.zone` stays default empty/false).
- Logs to `outputs/logs/`
  - Log rotation is enabled: `AI_LOG_MAX_BYTES` (default 10MB), `AI_LOG_BACKUP_COUNT` (default 5)
  - Runtime override: `AI_LOG_LEVEL`, `AI_LOG_FORMAT` (plain or json)
  - Config override: `AI_LOGGING_LEVEL`, `AI_LOGGING_FORMAT`
  - Metrics/heartbeat use dedicated loggers (`ai.metrics`, `ai.heartbeat`)
  - `events` / `events_accepted` increments when `emitter.emit()` accepts payload (`True`)
  - Actual backend delivery results are tracked separately as `backend_ack_ok` / `backend_ack_fail`
  - Sensor/Fusion counters: `sensor_packets_total`, `sensor_packets_dropped`, `sensor_source_errors`, `fusion_attempts`, `fusion_hits`, `fusion_misses`
  - Backend POST failures are logged with `BACKEND_*` error codes (not counted in `metrics.errors`)
  - Heartbeat payload includes `last_frame_age_sec`, `sensor_last_packet_age_sec`
- `max-events` counts accepted emits only (same `emitter.emit()==True` 기준)
- `--visualize` shows a debug window with bounding boxes
- `model.mode=real` requires `AI_MODEL_ADAPTER=module:ClassName`
- Multiple adapters can be set with a comma-separated list.
- `MODEL_CLASS_MAP_PATH` can provide class-to-event mapping (optional).
- `AI_MODEL_MODE` can override `model.mode` at runtime

## Mock Backend

- Run: `python -m ai.pipeline.mock_backend`
- Listens on `127.0.0.1:8080` and accepts `POST /api/events`
- Optional: override port via `MOCK_BACKEND_PORT` (e.g., `MOCK_BACKEND_PORT=18080`)

## Run Examples

1. Default run (posts to backend):
   - Windows: `./setup_env.ps1; python -m schnitzel_stream`
   - Linux: `PYTHONPATH=src python -m schnitzel_stream`

2. Dry run (no backend posts):
   - Windows: `./setup_env.ps1; python -m schnitzel_stream --dry-run --max-events 5`
   - Linux: `PYTHONPATH=src python -m schnitzel_stream --dry-run --max-events 5`

## Notes

- If backend is not running, you will see retry warnings.
- Replace `build_dummy_event` when real AI inference is ready.

## Code Mapping

- Entrypoint/CLI: `src/schnitzel_stream/cli/__main__.py`
- Default graph spec: `configs/graphs/legacy_pipeline.yaml`
- Phase 0 legacy job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- Pipeline core: `src/ai/pipeline/core.py`
- Async processor: `src/ai/pipeline/processor.py`
- Event builders: `src/ai/pipeline/events.py`
- Config loader: `src/ai/pipeline/config.py`, `src/ai/config.py`
- Sources: `src/ai/pipeline/sources/` (package: `file.py`, `rtsp.py`, `webcam.py`, `threaded.py`)
- Sensor runtime: `src/ai/pipeline/sensors/` (`protocol.py`, `loader.py`, `runtime.py`, `builder.py`, `fusion.py`)
- Sampler: `src/ai/pipeline/sampler.py`
- Visualizer: `src/ai/vision/visualizer.py`
- Emitters/backend: `src/ai/pipeline/emitters/` (compat shim: `src/ai/pipeline/emitter.py`), `src/ai/clients/backend_api.py`

---

## 한국어

파이프라인 명세
==============

## 엔트리포인트

- 엔트리포인트 모듈: `schnitzel_stream` (패키지)
- 레거시 런타임 패키지: `ai.pipeline` (Phase 0 job을 통해 실행)
- 윈도우 (권장): `./setup_env.ps1; python -m schnitzel_stream`
- 리눅스/수동: `PYTHONPATH=src python -m schnitzel_stream`

## 입력

- **비디오**: `data/samples/*.mp4` (기본값)
- **CLI 오버라이드**:
  - `--graph` (그래프 스펙 YAML 경로; 기본값: `configs/graphs/legacy_pipeline.yaml`; v2 그래프는 Phase 1 런타임 구현 전까지 `--validate-only`만 지원)
  - `--video` (mp4 경로; 파일 소스로 강제하며, 경로가 없으면 즉시 종료)
  - `--camera-id` (문자열; `configs/cameras.yaml`에 없으면 즉시 종료)
  - `--source-type` (file|rtsp|webcam|plugin; `--video`와 `--source-type rtsp/plugin` 조합은 불가)
  - `--camera-index` (정수; 웹캠 장치 인덱스 오버라이드, 기본값은 `cameras.yaml` `source.index` 또는 0)
  - `--validate-only` (그래프 스펙을 검증하고 실행 없이 종료)
  - `--dry-run` (백엔드 전송 안 함)
  - `--output-jsonl` (이벤트를 파일에 기록)
  - `--max-events` (전송 이벤트 수 제한)
  - `--visualize` (디버그 시각화 창 표시)
  - `--loop` (비디오 파일 무한 루프; 파일 소스 전용)

## 설정 (`configs/default.yaml` + `configs/cameras.yaml`에서 로드)

- 선택 런타임 프로필 오버레이: `app.env` 값에 따라 `configs/dev.yaml` 또는 `configs/prod.yaml`
- `app.site_id` -> 이벤트 site_id
- `app.timezone` -> 이벤트 ts 타임존
- `ingest.fps_limit` -> 다운샘플링 FPS
- `source.adapter` -> 선택적 입력 소스 플러그인 (`module:ClassName`, `source.type=plugin`에서 사용)
- `sensor.*` -> 멀티모달 센서 축 설정 (`enabled`, `type`, `adapter`, `topic`, `queue_size`, `time_window_ms`, `emit_events`, `emit_fused_events`)
  - P2 기준 동작:
    - 각 비전 이벤트 `sensor` 필드에 최근 패킷 주입
    - `sensor.emit_events=true`면 독립 `SENSOR_EVENT` 전송
    - `sensor.emit_fused_events=true`면 추가 `FUSED_EVENT` 전송
- `events.post_url` -> 백엔드 엔드포인트
- `events.timeout_sec` -> 요청 타임아웃
- `events.emitter_adapter` -> 선택적 커스텀 출력 emitter (`module:ClassName`)
- `events.retry.max_attempts` / `events.retry.backoff_sec`
- `events.snapshot.base_dir` / `events.snapshot.public_prefix`
- 스냅샷은 기본적으로 비활성화되어 있으며, `events.snapshot.base_dir` 설정 시 활성화됨.
- 멀티 카메라 설정은 `configs/cameras.yaml`의 `cameras:` 항목 아래에 위치할 수 있음.
- 웹캠 소스는 `configs/cameras.yaml`에서 `source.index`를 지정할 수 있음.
- 설정 파일 상대경로(예: 파일 소스 경로, zones 파일 경로)는 repo root 기준 절대경로로 해석됨.
- `zones.*` 및 `rules.rule_point_by_event_type`이 구역 로딩 및 내부 판정을 제어함.

## 출력 페이로드 (더미, protocol.md 준수)

- `event_id` (uuid 문자열)
- `ts` (ISO-8601, app.timezone 설정 사용)
- `site_id` (문자열)
- `camera_id` (문자열)
- `event_type` = 비전 이벤트 타입(예: "ZONE_INTRUSION"), 센서 확장 시 `SENSOR_EVENT`, `FUSED_EVENT` 가능
- `object_type` = "PERSON"
- `severity` = "LOW"
- `track_id` (정수 또는 null; PERSON의 경우 필수)
- `bbox` = `{x1,y1,x2,y2}`
- `confidence` = 0.75 (MockModelEventBuilder)
- `zone` = `{zone_id, inside}`
- `snapshot_path` = 스냅샷 활성화 시 저장된 경로 문자열, 아니면 null
- `sensor` = 선택 객체 (시간창 `sensor.time_window_ms` 내 최근 패킷), 없으면 null

## 멀티 이벤트 지원

- 빌더는 페이로드 리스트를 반환함(프레임당 `0..N` 이벤트).
- 파이프라인은 리스트 순서대로 각 페이로드를 전송함.

## 모델 연동 (실사용 우선)

- `configs/default.yaml` -> `model.mode`
  - `real` (기본값): `model.adapter` / `AI_MODEL_ADAPTER` 필요, 누락 시 시작 즉시 실패
    - 기본 `CustomModelAdapter`는 템플릿이므로 구현 전에는 fail-fast
  - `mock`: 테스트 전용 모드이며 `AI_MODEL_MODE=mock`처럼 명시적으로만 사용
  - 기타 값: 시작 시 즉시 실패(fail-fast)
- 모델/트래커 출력은 동일한 페이로드 키를 가져야 함:
  - `bbox`, `confidence`, `track_id` (PERSON 필수), `event_type`, `object_type`, `severity`

## 동작 방식

- OpenCV를 사용하여 프레임 읽기
- FPS 제한에 따른 프레임 샘플링
- 샘플링은 목표 FPS를 초과하지 않도록 비율 기반 선택기 사용
- 모크 빌더는 명시적 `model.mode=mock`에서만 중복 제거 비활성화 시 프레임당 하나의 더미 이벤트 생성
- 실제 빌더는 프레임당 0..N개의 이벤트 리스트 반환 가능
- `source.type=plugin`이면 입력 소스를 `source.adapter` / `AI_SOURCE_ADAPTER`로 로드함
- `sensor.enabled=true`이면 센서 플러그인을 `sensor.adapter` / `AI_SENSOR_ADAPTER`(단일) 또는 `sensor.adapters` / `AI_SENSOR_ADAPTERS`(다중)로 로드함
- 센서 축은 `sensor.time_window_ms` 기준으로 최근 패킷을 각 이벤트의 `sensor` 필드에 주입함
- `sensor.emit_events=true`이면 센서 축에서 독립 `SENSOR_EVENT`를 추가 전송함
- `sensor.emit_fused_events=true`이면 융합 래퍼가 추가 `FUSED_EVENT`를 전송함
- 최종 위험/알람 판단은 기본적으로 런타임 범위 밖이며, 런타임은 근거 이벤트를 전달하고 최종 액션은 사용자 운영 정책에서 결정함. (백엔드 정책 계층은 선택 사항) 다만 배포 정책에 따라 런타임 내부 룰/플러그인 단계로 최종 판단까지 확장할 수 있음.
- `events.emitter_adapter`가 설정되면 커스텀 emitter 플러그인을 로드함
- 내장 ROS2 플러그인 템플릿 경로:
  - source: `ai.plugins.ros2.image_source:Ros2ImageSource`
  - emitter: `ai.plugins.ros2.event_emitter:Ros2EventEmitter`
  - 필요 패키지: `rclpy`, `sensor_msgs`, `std_msgs`
- 내장 무실장비 센서 템플릿:
  - sensor adapter: `ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource`
- 백엔드 호스트 해석 불가 시 stdout으로 폴백 (dry-run)
- **백엔드 재시도 정책**: HTTP 4xx 응답은 재시도 없이 드롭 (클라이언트 오류); 5xx 또는 네트워크 오류만 지수 백오프로 재시도.
- 유효하지 않은 카메라 ID는 시작 시 즉시 실패
- 유효하지 않은 타임존은 UTC로 폴백
- RTSP 소스의 경우, 읽기 실패 시 backoff+jitter를 포함한 재시도 수행
  - `rtsp.max_attempts` 초과 시 재연결 중단 및 파이프라인 종료.
- RTSP 재연결 성공 후 타이트 루프 방지를 위해 0.2초 지연 적용.
- **RTSP 전송 프로토콜**: 패킷 손실 및 영상 깨짐 방지를 위해 기본값 `tcp` 사용. 초저지연이 필요한 경우 `AI_RTSP_TRANSPORT=udp` 환경 변수로 오버라이드 가능.
- **FPS 조절(Throttling)**: `is_live=False`인 파일 소스에만 적용됨. RTSP 등 라이브 소스는 수신 버퍼 누적(Latnecy/Corrupt) 방지를 위해 인위적인 대기 없이 즉시 처리함.
- **부드러운 시각화**: `--visualize` 활성화 시 모든 프레임을 화면에 표시(샘플링된 프레임만이 아님). 마지막 분석의 탐지 박스를 유지하여 깜빡임 방지. OpenCV의 메모리 재사용으로 인한 잔상(Buffer Staining) 방지를 위해 시각화 시 프레임 복사본을 생성하여 사용함. 여러 카메라 실행 시 창 겹침 방지를 위해 고유한 창 이름(`AI Pipeline - <camera_id>`)을 사용함.
- **스레드 프레임 리더**: 라이브 소스(`is_live=True`)는 자동으로 `ThreadedSource`로 래핑되어 백그라운드 스레드에서 프레임을 수신한다. 모델 추론이 `source.read()`를 블로킹하여 발생하는 프레임 드롭/디코더 깨짐을 방지한다.
- **비동기 프레임 처리 (Display-First)**: 라이브 소스(`is_live=True`)에서 `FrameProcessor`는 백그라운드 워커 스레드에서 추론을 수행한다. 추론 직후 디스플레이 결과를 즉시 갱신한 뒤 zone 평가와 전송을 수행하여, zone API fetch 지연이 화면 표시를 차단하지 않는다. 파일 소스(`is_live=False`)는 프레임 순서 보장을 위해 동기 처리를 유지한다.
- **비차단 Zone API 갱신**: `zones.source=api`일 때 zone fetch는 백그라운드에서 비동기 갱신된다. 이벤트 처리 경로는 캐시(만료 캐시 포함)를 우선 사용하므로 zone API 일시 장애가 추론 경로를 직접 블로킹하지 않는다.
- `AI_ZONES_SOURCE`로 실행 시 `zones.source` 오버라이드 가능 (`file`, `api`, `none`).
  - `none`이면 zone 평가를 비활성화하고 `payload.zone`은 기본값(빈 zone_id/inside=false)을 유지한다.
- 로그는 `outputs/logs/`에 저장
  - 로그 로테이션 활성화: `AI_LOG_MAX_BYTES` (기본 10MB), `AI_LOG_BACKUP_COUNT` (기본 5)
  - 런타임 오버라이드: `AI_LOG_LEVEL`, `AI_LOG_FORMAT` (plain 또는 json)
  - 설정 오버라이드: `AI_LOGGING_LEVEL`, `AI_LOGGING_FORMAT`
  - 메트릭/하트비트는 전용 로거 사용 (`ai.metrics`, `ai.heartbeat`)
  - `events` / `events_accepted`는 `emitter.emit()`이 payload를 수락(`True`)할 때 증가
  - 실제 백엔드 전달 결과는 `backend_ack_ok` / `backend_ack_fail`로 별도 집계
  - 센서/융합 카운터: `sensor_packets_total`, `sensor_packets_dropped`, `sensor_source_errors`, `fusion_attempts`, `fusion_hits`, `fusion_misses`
  - 백엔드 POST 실패는 `BACKEND_*` 에러 코드 로그로 남으며 `metrics.errors`에는 반영되지 않음
  - 하트비트 페이로드에 `last_frame_age_sec`, `sensor_last_packet_age_sec` 포함
- `max-events`는 수락된 emit 횟수(`emitter.emit()==True`)를 카운트함
- `--visualize`는 바운딩 박스를 포함한 디버그 창 표시
- `model.mode=real` 사용 시 `AI_MODEL_ADAPTER=module:ClassName` 설정 필요
- 복수 어댑터는 콤마로 구분하여 설정 가능.
- `MODEL_CLASS_MAP_PATH`로 클래스-이벤트 매핑 제공 가능 (옵션).
- `AI_MODEL_MODE`로 실행 시 `model.mode` 오버라이드 가능

## 모크 백엔드

- 실행: `python -m ai.pipeline.mock_backend`
- `127.0.0.1:8080`에서 수신하며 `POST /api/events` 허용
- 옵션: `MOCK_BACKEND_PORT`로 포트 변경 가능

## 실행 예시

1. 기본 실행 (백엔드 전송):
   - 윈도우: `./setup_env.ps1; python -m schnitzel_stream`
   - 리눅스: `PYTHONPATH=src python -m schnitzel_stream`

2. 드라이런 (백엔드 전송 안 함):
   - 윈도우: `./setup_env.ps1; python -m schnitzel_stream --dry-run --max-events 5`
   - 리눅스: `PYTHONPATH=src python -m schnitzel_stream --dry-run --max-events 5`

## 참고 사항

- 백엔드가 실행 중이 아니면 재시도 경고가 표시됨.
- 실제 AI 추론이 준비되면 `build_dummy_event`를 교체할 것.

## 코드 매핑

- 엔트리/CLI: `src/schnitzel_stream/cli/__main__.py`
- 기본 그래프 스펙: `configs/graphs/legacy_pipeline.yaml`
- Phase 0 레거시 job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 파이프라인 코어: `src/ai/pipeline/core.py`
- 비동기 프로세서: `src/ai/pipeline/processor.py`
- 이벤트 빌더: `src/ai/pipeline/events.py`
- 설정 로더: `src/ai/pipeline/config.py`, `src/ai/config.py`
- 소스: `src/ai/pipeline/sources/` (`file.py`, `rtsp.py`, `webcam.py`, `threaded.py`)
- 센서 런타임: `src/ai/pipeline/sensors/` (`protocol.py`, `loader.py`, `runtime.py`, `builder.py`, `fusion.py`)
- 샘플러: `src/ai/pipeline/sampler.py`
- 시각화: `src/ai/vision/visualizer.py`
- 에미터/백엔드: `src/ai/pipeline/emitters/` (호환 shim: `src/ai/pipeline/emitter.py`), `src/ai/clients/backend_api.py`
