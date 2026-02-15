# Command Reference

## English

Command Reference
==================

Complete reference for all CLI commands, scripts, and environment variables.

Prerequisites
-------------

```powershell
# Windows — set PYTHONPATH (required once per terminal session)
./setup_env.ps1

# Linux / macOS
export PYTHONPATH=src
```

---

1. Entrypoint (`python -m schnitzel_stream`)
--------------------------------------

Universal stream platform entrypoint (SSOT).

Defaults:
- Default graph (v2): `configs/graphs/dev_vision_e2e_mock_v2.yaml`
- Legacy graph (v1): `configs/graphs/legacy_pipeline.yaml` (deprecated; runs `legacy/ai/**` via `src/ai` shim)

Note:
- `python -m schnitzel_stream` supports both v1 (legacy job graph) and v2 (node graph).
- This doc contains many **legacy(v1)** examples. For legacy runs, explicitly pass `--graph configs/graphs/legacy_pipeline.yaml`.
- Typical v2 runs use `--graph`, `--validate-only`, `--max-events`, and `--report-json`.
- v2 examples: `configs/graphs/dev_vision_e2e_mock_v2.yaml`, `configs/graphs/dev_inproc_demo_v2.yaml`, `configs/graphs/dev_durable_*_v2.yaml`, `configs/graphs/dev_rtsp_frames_v2.yaml`, `configs/graphs/dev_webcam_frames_v2.yaml`.
- v2 node config reserved key: `config.__runtime__` (runner behavior, not passed to plugins)
  - `inbox_max` (int): per-node inbox limit (backpressure)
  - `inbox_overflow` (`drop_new`|`drop_oldest`|`error`): overflow policy

### CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--graph` | string | `configs/graphs/dev_vision_e2e_mock_v2.yaml` | Graph spec YAML path (default: v2 node graph; v1 legacy job graph is deprecated) |
| `--camera-id` | string | auto (from config) | Camera ID (must exist in `configs/cameras.yaml`) |
| `--video` | string | `data/samples/*.mp4` | Video file path (forces file source) |
| `--source-type` | file\|rtsp\|webcam\|plugin | auto | Override source type |
| `--camera-index` | int | from camera config or 0 | Webcam device index override |
| `--validate-only` | flag | off | Validate graph spec and exit without running |
| `--report-json` | flag | off | Print JSON run report (v2 in-proc runtime only) |
| `--dry-run` | flag | off | Do not POST to backend (stdout only) |
| `--output-jsonl` | string | none | Write events to JSONL file |
| `--max-events` | int | unlimited | Stop after N successful emits |
| `--visualize` | flag | off | Show debug window with bounding boxes |
| `--loop` | flag | off | Loop video file (file source only) |

### Usage by Scenario

For local tests without a configured real adapter, enable explicit mock mode first:

```powershell
# PowerShell
$env:AI_MODEL_MODE="mock"

# Linux / macOS
export AI_MODEL_MODE=mock
```

**0) Validate graph spec (no run)**

```powershell
# default v2 graph
python -m schnitzel_stream validate

# legacy v1 graph
python -m schnitzel_stream validate --graph configs/graphs/legacy_pipeline.yaml
```

**0a) Run v2 in-proc demo graph**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
```

**0b) Durable queue demo (enqueue + drain)**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
```

**0c) Run v2 webcam frame graph**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml --max-events 30
```

**1) First-time quick test (no backend needed)**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --dry-run `
  --max-events 5
```

Reads `data/samples/*.mp4`, prints 5 events to stdout, exits.

**2) Save events to file for analysis**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --output-jsonl outputs/events.jsonl `
  --max-events 20
```

**3) Specific video file**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --dry-run
```

**4) Specific video file with visualization**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --visualize `
  --dry-run
```

Use `Ctrl+C` in terminal to stop.

**5) Infinite loop playback (demo/benchmark)**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --loop `
  --visualize `
  --dry-run
```

**6) Webcam**

```powershell
python -m schnitzel_stream `
  --source-type webcam `
  --camera-index 0 `
  --visualize `
  --dry-run
```

**7) Plugin I/O (ROS2 example)**

```powershell
# Source plugin: ROS2 image topic
$env:AI_SOURCE_TYPE="plugin"
$env:AI_SOURCE_ADAPTER="ai.plugins.ros2.image_source:Ros2ImageSource"
$env:AI_ROS2_SOURCE_TOPIC="/camera/image_raw/compressed"

# Emitter plugin: ROS2 event topic
$env:AI_EVENTS_EMITTER_ADAPTER="ai.plugins.ros2.event_emitter:Ros2EventEmitter"
$env:AI_ROS2_EVENT_TOPIC="/ai/events"

python -m schnitzel_stream `
  --max-events 20
```

Requires ROS2 Python packages (`rclpy`, `sensor_msgs`, `std_msgs`; `cv_bridge` only when `AI_ROS2_SOURCE_MSG_TYPE=image`).

**7a) Sensor lane (no-hardware fake ultrasonic)**

```powershell
$env:AI_SENSOR_ENABLED="true"
$env:AI_SENSOR_TYPE="ultrasonic"
$env:AI_SENSOR_ADAPTER="ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource"
$env:AI_SENSOR_TIME_WINDOW_MS="5000"
$env:AI_SENSOR_EMIT_EVENTS="true"
$env:AI_SENSOR_EMIT_FUSED_EVENTS="true"
$env:AI_MODEL_MODE="mock"

python -m schnitzel_stream `
  --output-jsonl outputs/events_sensor.jsonl `
  --max-events 8
```

**7b) Multi-sensor lane (comma-separated adapters)**

```powershell
$env:AI_SENSOR_ENABLED="true"
$env:AI_SENSOR_ADAPTERS = `
  "ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource," + `
  "ai.plugins.sensors.serial_ultrasonic:SerialUltrasonicSensorSource"
$env:AI_SENSOR_TIME_WINDOW_MS="5000"
$env:AI_MODEL_MODE="mock"

python -m schnitzel_stream `
  --dry-run `
  --max-events 20
```

**8) RTSP camera (specific camera from config)**

For real-mode runs (especially scenarios 8-10), configure a concrete adapter first:
`AI_MODEL_ADAPTER=module:ClassName` (default `CustomModelAdapter` is template/fail-fast).

```powershell
python -m schnitzel_stream --camera-id cam01
```

Uses RTSP URL from `configs/cameras.yaml`. Posts to the configured backend.

**9) RTSP with visualization (live monitoring)**

```powershell
python -m schnitzel_stream `
  --camera-id cam01 `
  --visualize
```

**10) Full production run**

```powershell
python -m schnitzel_stream --camera-id cam01
```

No `--dry-run`, no `--max-events` — runs continuously, posts to backend.

**11) Invalid combinations (will error)**

```powershell
# --video + --source-type rtsp/plugin is not allowed
python -m schnitzel_stream --video test.mp4 --source-type rtsp    # ERROR
python -m schnitzel_stream --video test.mp4 --source-type plugin  # ERROR
```

---

2. Mock Backend (`python -m ai.pipeline.mock_backend`)
-------------------------------------------------------

Lightweight HTTP server that accepts `POST /api/events`. Useful for local testing.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_BACKEND_HOST` | `127.0.0.1` | Listen host |
| `MOCK_BACKEND_PORT` | `8080` | Listen port |

### Usage

**Terminal 1 — start mock backend:**

```powershell
python -m ai.pipeline.mock_backend
```

**Terminal 2 — run pipeline (posts to mock):**

```powershell
python -m schnitzel_stream --max-events 5
```

Events appear in Terminal 1 logs.

**Custom port:**

```powershell
$env:MOCK_BACKEND_PORT = "18080"
python -m ai.pipeline.mock_backend
```

---

3. Multi-Camera (`python scripts/multi_cam.py`)
-------------------------------------------------

Launches/stops multiple pipeline processes (one per camera) based on `configs/cameras.yaml`.

### Commands

```powershell
python scripts/multi_cam.py start                    # Start all enabled cameras
python scripts/multi_cam.py start --cameras cam01,cam02  # Start specific cameras
python scripts/multi_cam.py status                   # Check running status
python scripts/multi_cam.py stop                     # Stop all pipelines
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--config`, `-c` | `configs/cameras.yaml` | Camera config file |
| `--log-dir`, `-l` | OS temp dir | Log and PID file directory |
| `--cameras` | all enabled | Comma-separated camera IDs |
| `--extra-args` | none | Extra args passed to pipeline (e.g. `"--dry-run"`) |

### Example: dry-run all cameras

```powershell
python scripts/multi_cam.py start --extra-args "--dry-run --max-events 10"
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

---

4. RTSP E2E Test (`python scripts/check_rtsp.py`)
---------------------------------------------------

Automated RTSP stability test: starts MediaMTX + ffmpeg + mock backend + pipeline, simulates disconnect/reconnect, verifies recovery.

**Requirements:** `ffmpeg` installed and in PATH. MediaMTX is auto-downloaded.

### Usage

```powershell
python scripts/check_rtsp.py                 # Run test
python scripts/check_rtsp.py --strict        # Fail on recovery failure
python scripts/check_rtsp.py --log-dir C:\logs\rtsp_test
```

### What it does

1. Starts MediaMTX (RTSP server)
2. Starts mock backend
3. Starts ffmpeg (publishes video to RTSP)
4. Starts pipeline (consumes RTSP)
5. Waits for initial events
6. Kills ffmpeg (simulates disconnect)
7. Restarts ffmpeg
8. Verifies pipeline recovers and emits new events

---

5. Regression Check (`python scripts/regression_check.py`)
------------------------------------------------------------

Runs pipeline on sample video, compares output against golden reference to detect regressions.
The helper script explicitly sets `AI_MODEL_MODE=mock` to keep regression signals deterministic.

### Usage

```powershell
# Run regression check (compare against golden)
python scripts/regression_check.py --max-events 5

# Update golden reference (after intentional changes)
python scripts/regression_check.py --max-events 5 --update-golden
```

Output: `regression_ok` or `regression_failed` with diff details.

---

6. Accuracy Evaluation (`python scripts/accuracy_eval.py`)
-----------------------------------------------------------

Evaluates model accuracy against ground truth labels. Requires a real model adapter.

### Usage

```powershell
python scripts/accuracy_eval.py ^
  --gt data/labels/ground_truth.jsonl ^
  --adapter "ai.vision.adapters.yolo_adapter:YOLOAdapter" ^
  --conf 0.25 --iou 0.5 ^
  --out metrics_summary.json
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gt` | required | Ground truth JSONL file |
| `--adapter` | required | Model adapter (`module:Class`) |
| `--class-map` | none | Class mapping YAML |
| `--conf` | 0.25 | Confidence threshold |
| `--iou` | 0.5 | IoU threshold |
| `--out` | `metrics_summary.json` | Output file |

---

7. Tests (`pytest`)
------------------------------

### Usage

```text
# Windows PowerShell (once per session)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"

# Linux/macOS
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/regression/ -v

# Run specific test file
pytest tests/unit/pipeline/test_frame_processor.py -v

# Run specific test
pytest tests/unit/pipeline/test_frame_processor.py::test_processor_stop -v
```

### Test Hygiene (duplicate/meaningless checks)

Use the static hygiene checker to detect:

- near-duplicate test bodies (constant-normalized)
- tests without assertion intent (`assert`, `pytest.raises`, or `assert*` helper calls)
- trivial `assert True` tests

```text
# Cross-platform (Windows/Linux/macOS)
python scripts/test_hygiene.py

# Strict gate (fail when issues exceed thresholds)
python scripts/test_hygiene.py --strict

# Baseline gate (ratchet: fail only when hygiene gets worse)
python scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0

# Save JSON report
python scripts/test_hygiene.py --json-out outputs/test_hygiene_report.json
```

---

8. Environment Variables
-------------------------

### Core Pipeline (`AI_*`)

| Variable | Maps to config | Default | Description |
|----------|---------------|---------|-------------|
| `AI_EVENTS_POST_URL` | `events.post_url` | `http://localhost:8080/api/events` | Backend URL |
| `AI_INGEST_FPS_LIMIT` | `ingest.fps_limit` | `10` | Frame rate limit |
| `AI_SOURCE_TYPE` | `source.type` | `file` | `file`, `rtsp`, `webcam`, or `plugin` |
| `AI_SOURCE_ADAPTER` | `source.adapter` | none | Source plugin path (`module:ClassName`, used with `AI_SOURCE_TYPE=plugin`) |
| `AI_SENSOR_ENABLED` | `sensor.enabled` | `false` | Sensor lane switch (attach nearest sensor packet into event `sensor` field) |
| `AI_SENSOR_TYPE` | `sensor.type` | none | Sensor lane type (`ros2`, `mqtt`, `modbus`, `serial`, `plugin`) |
| `AI_SENSOR_ADAPTER` | `sensor.adapter` | none | Sensor plugin path (`module:ClassName`) |
| `AI_SENSOR_ADAPTERS` | `sensor.adapters` | none | Multi-sensor adapter paths (comma-separated, e.g. `a:Front,b:Rear`) |
| `AI_SENSOR_TOPIC` | `sensor.topic` | none | Sensor source topic/channel hint |
| `AI_SENSOR_QUEUE_SIZE` | `sensor.queue_size` | `256` | Sensor queue size |
| `AI_SENSOR_TIME_WINDOW_MS` | `sensor.time_window_ms` | `300` | Event-sensor matching time-window (ms) |
| `AI_SENSOR_EMIT_EVENTS` | `sensor.emit_events` | `false` | Emit independent `SENSOR_EVENT` payloads |
| `AI_SENSOR_EMIT_FUSED_EVENTS` | `sensor.emit_fused_events` | `false` | Emit additional `FUSED_EVENT` payloads |
| `AI_FAKE_SENSOR_ID` | plugin-only | `ultrasonic-front-01` | Fake ultrasonic sensor id |
| `AI_FAKE_SENSOR_INTERVAL_SEC` | plugin-only | `0.05` | Fake ultrasonic publish interval sec |
| `AI_MODEL_MODE` | `model.mode` | `real` | `real` or `mock` (`mock` is test-only explicit mode) |
| `AI_MODEL_ADAPTER` | `model.adapter` | `ai.vision.adapters.custom_adapter:CustomModelAdapter` | Adapter path (default template fails fast until implemented; e.g. `ai.vision.adapters.yolo_adapter:YOLOAdapter`) |
| `AI_ZONES_SOURCE` | `zones.source` | `api` | `api`, `file`, or `none` (`none` disables zone evaluation) |
| `AI_RTSP_TRANSPORT` | `rtsp.transport` | `tcp` | `tcp` or `udp` |
| `AI_RTSP_TIMEOUT_SEC` | `rtsp.timeout_sec` | `5.0` | Connection timeout |
| `AI_RTSP_MAX_ATTEMPTS` | `rtsp.max_attempts` | `0` (infinite) | Reconnect limit |
| `AI_EVENTS_SNAPSHOT_BASE_DIR` | `events.snapshot.base_dir` | none (disabled) | Snapshot save dir |
| `AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX` | `events.snapshot.public_prefix` | none | Snapshot URL prefix |
| `AI_EVENTS_EMITTER_ADAPTER` | `events.emitter_adapter` | none | Custom emitter plugin path (`module:ClassName`) |
| `AI_ROS2_SOURCE_TOPIC` | plugin-only | `/camera/image_raw/compressed` | ROS2 source topic |
| `AI_ROS2_SOURCE_MSG_TYPE` | plugin-only | `compressed` | `compressed` or `image` |
| `AI_ROS2_SOURCE_NODE_NAME` | plugin-only | `ai_frame_source` | ROS2 source node name |
| `AI_ROS2_SOURCE_QOS_DEPTH` | plugin-only | `10` | ROS2 source QoS depth |
| `AI_ROS2_SOURCE_READ_TIMEOUT_SEC` | plugin-only | `1.0` | Source read timeout sec |
| `AI_ROS2_SOURCE_FPS_HINT` | plugin-only | `0` | Source fps hint |
| `AI_ROS2_EVENT_TOPIC` | plugin-only | `/ai/events` | ROS2 emitter topic |
| `AI_ROS2_EMITTER_NODE_NAME` | plugin-only | `ai_event_emitter` | ROS2 emitter node name |
| `AI_ROS2_EMITTER_QOS_DEPTH` | plugin-only | `100` | ROS2 emitter QoS depth |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `AI_LOG_FORMAT` | `plain` | `plain` or `json` |
| `AI_LOG_MAX_BYTES` | `10485760` (10MB) | Max log file size before rotation |
| `AI_LOG_BACKUP_COUNT` | `5` | Number of rotated log files |

### Model / Tracker (adapter-level)

| Variable | Default | Description |
|----------|---------|-------------|
| `YOLO_MODEL_PATH` | required | Path to YOLO `.pt` file |
| `YOLO_CONF` | `0.25` | Confidence threshold |
| `YOLO_DEVICE` | `auto` | `auto`, `cpu`, or CUDA device |
| `ONNX_MODEL_PATH` | required | Path to ONNX `.onnx` file |
| `ONNX_CONF` | `0.25` | Confidence threshold |
| `ONNX_IOU` | `0.45` | NMS IoU threshold |
| `ONNX_PROVIDERS` | `CUDAExecutionProvider,CPUExecutionProvider` | Execution providers |
| `MODEL_CLASS_MAP_PATH` | `configs/model_class_map.yaml` | Class-to-event mapping |
| `TRACKER_TYPE` | `none` | `none`, `iou`, or `bytetrack` |
| `TRACKER_MAX_AGE` | `30` | Max unmatched frames |
| `TRACKER_MIN_HITS` | `1` | Min detections to start track |
| `TRACKER_IOU` | `0.3` | Tracking IoU threshold |

---

9. Config Files
----------------

| File | Purpose |
|------|---------|
| `configs/default.yaml` | Base pipeline settings |
| `configs/cameras.yaml` | Multi-camera definitions (id, source type, URL/path) |
| `configs/model_class_map.yaml` | Class ID to event type mapping |
| `.env.example` | All env vars with example values |

### Config resolution order

1. `configs/default.yaml` + `configs/cameras.yaml` merge (base)
2. Runtime profile overlay (`configs/dev.yaml` or `configs/prod.yaml`, via `app.env`)
3. Environment variable overrides (`AI_*`)
4. CLI/runtime overrides for execution arguments (`--graph`, `--camera-id`, `--video`, `--source-type`, `--camera-index`, `--validate-only`, `--report-json`, `--dry-run`, `--output-jsonl`, `--max-events`, `--visualize`, `--loop`)

---

## 한국어

명령어 레퍼런스
================

모든 CLI 명령어, 스크립트, 환경 변수에 대한 종합 레퍼런스.

사전 준비
---------

```powershell
# Windows — PYTHONPATH 설정 (터미널 세션당 1회)
./setup_env.ps1

# Linux / macOS
export PYTHONPATH=src
```

---

1. 엔트리포인트 (`python -m schnitzel_stream`)
-----------------------------------------

범용 스트림 플랫폼 엔트리포인트(SSOT).

기본값:
- 기본 그래프(v2): `configs/graphs/dev_vision_e2e_mock_v2.yaml`
- 레거시 그래프(v1): `configs/graphs/legacy_pipeline.yaml` (deprecated; `legacy/ai/**` 실행, `src/ai` shim)

참고:
- `python -m schnitzel_stream`는 v1(레거시 job 그래프)과 v2(node graph)를 모두 지원합니다.
- 이 문서의 많은 예시는 **레거시(v1)** 기준입니다. 레거시 실행은 `--graph configs/graphs/legacy_pipeline.yaml`를 명시하세요.
- v2 실행은 보통 `--graph`, `--validate-only`, `--max-events`, `--report-json`만 사용합니다.
- v2 예시: `configs/graphs/dev_vision_e2e_mock_v2.yaml`, `configs/graphs/dev_inproc_demo_v2.yaml`, `configs/graphs/dev_durable_*_v2.yaml`, `configs/graphs/dev_rtsp_frames_v2.yaml`, `configs/graphs/dev_webcam_frames_v2.yaml`.
- v2 노드 설정 예약 키: `config.__runtime__` (러너 동작 제어, 플러그인에는 전달되지 않음)
  - `inbox_max` (정수): 노드별 inbox 제한(백프레셔)
  - `inbox_overflow` (`drop_new`|`drop_oldest`|`error`): overflow 정책

### CLI 옵션

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `--graph` | 문자열 | `configs/graphs/dev_vision_e2e_mock_v2.yaml` | 그래프 스펙 YAML 경로 (기본값: v2 node graph; v1 레거시 job 그래프는 deprecated) |
| `--camera-id` | 문자열 | 자동 (설정 기반) | 카메라 ID (`configs/cameras.yaml`에 존재해야 함) |
| `--video` | 문자열 | `data/samples/*.mp4` | 비디오 파일 경로 (파일 소스 강제) |
| `--source-type` | file\|rtsp\|webcam\|plugin | 자동 | 소스 타입 오버라이드 |
| `--camera-index` | 정수 | 카메라 설정값 또는 0 | 웹캠 장치 인덱스 오버라이드 |
| `--validate-only` | 플래그 | off | 그래프 스펙 검증 후 실행 없이 종료 |
| `--report-json` | 플래그 | off | JSON 실행 리포트 출력 (v2 in-proc 런타임 전용) |
| `--dry-run` | 플래그 | off | 백엔드 전송 안 함 (stdout만) |
| `--output-jsonl` | 문자열 | 없음 | 이벤트를 JSONL 파일에 저장 |
| `--max-events` | 정수 | 무제한 | N번 전송 후 종료 |
| `--visualize` | 플래그 | off | 바운딩 박스 디버그 창 표시 |
| `--loop` | 플래그 | off | 비디오 무한 루프 (파일 소스 전용) |

### 상황별 사용법

실제 어댑터가 아직 설정되지 않았다면, 로컬 테스트 전에 mock 모드를 먼저 명시:

```powershell
# PowerShell
$env:AI_MODEL_MODE="mock"

# Linux / macOS
export AI_MODEL_MODE=mock
```

**0) 그래프 스펙만 검증 (실행 안 함)**

```powershell
# 기본 v2 그래프
python -m schnitzel_stream validate

# 레거시 v1 그래프
python -m schnitzel_stream validate --graph configs/graphs/legacy_pipeline.yaml
```

**0a) v2 in-proc 데모 그래프 실행**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
```

**0b) Durable queue 데모 (enqueue + drain)**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
```

**0c) v2 웹캠 프레임 그래프 실행**

```powershell
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml --max-events 30
```

**1) 처음 빠르게 테스트 (백엔드 불필요)**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --dry-run `
  --max-events 5
```

`data/samples/*.mp4`를 읽고, stdout에 이벤트 5개 출력 후 종료.

**2) 이벤트를 파일로 저장해서 분석**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --output-jsonl outputs/events.jsonl `
  --max-events 20
```

**3) 특정 비디오 파일 지정**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --dry-run
```

**4) 시각화와 함께 특정 비디오 실행**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --visualize `
  --dry-run
```

종료는 터미널에서 `Ctrl+C`를 사용.

**5) 무한 루프 재생 (데모/벤치마크)**

```powershell
python -m schnitzel_stream `
  --graph configs/graphs/legacy_pipeline.yaml `
  --video C:\Videos\test.mp4 `
  --loop `
  --visualize `
  --dry-run
```

**6) 웹캠**

```powershell
python -m schnitzel_stream `
  --source-type webcam `
  --camera-index 0 `
  --visualize `
  --dry-run
```

**7) 플러그인 입출력 (ROS2 예시)**

```powershell
# 입력 플러그인: ROS2 이미지 토픽
$env:AI_SOURCE_TYPE="plugin"
$env:AI_SOURCE_ADAPTER="ai.plugins.ros2.image_source:Ros2ImageSource"
$env:AI_ROS2_SOURCE_TOPIC="/camera/image_raw/compressed"

# 출력 플러그인: ROS2 이벤트 토픽
$env:AI_EVENTS_EMITTER_ADAPTER="ai.plugins.ros2.event_emitter:Ros2EventEmitter"
$env:AI_ROS2_EVENT_TOPIC="/ai/events"

python -m schnitzel_stream `
  --max-events 20
```

필수 패키지: `rclpy`, `sensor_msgs`, `std_msgs` (`AI_ROS2_SOURCE_MSG_TYPE=image` 사용 시 `cv_bridge` 추가 필요).

**7a) 센서 축 (무실장비 fake 초음파)**

```powershell
$env:AI_SENSOR_ENABLED="true"
$env:AI_SENSOR_TYPE="ultrasonic"
$env:AI_SENSOR_ADAPTER="ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource"
$env:AI_SENSOR_TIME_WINDOW_MS="5000"
$env:AI_SENSOR_EMIT_EVENTS="true"
$env:AI_SENSOR_EMIT_FUSED_EVENTS="true"
$env:AI_MODEL_MODE="mock"

python -m schnitzel_stream `
  --output-jsonl outputs/events_sensor.jsonl `
  --max-events 8
```

**7b) 멀티 센서 축 (콤마 구분 어댑터)**

```powershell
$env:AI_SENSOR_ENABLED="true"
$env:AI_SENSOR_ADAPTERS = `
  "ai.plugins.sensors.fake_ultrasonic:FakeUltrasonicSensorSource," + `
  "ai.plugins.sensors.serial_ultrasonic:SerialUltrasonicSensorSource"
$env:AI_SENSOR_TIME_WINDOW_MS="5000"
$env:AI_MODEL_MODE="mock"

python -m schnitzel_stream `
  --dry-run `
  --max-events 20
```

**8) RTSP 카메라 (설정 파일 기반)**

실제 모드 실행(특히 8-10번) 전에는 실제 어댑터를 설정해야 함:
`AI_MODEL_ADAPTER=module:ClassName` (기본 `CustomModelAdapter`는 템플릿/fail-fast).

```powershell
python -m schnitzel_stream --camera-id cam01
```

`configs/cameras.yaml`의 RTSP URL 사용. 설정된 백엔드로 전송.

**9) RTSP + 시각화 (실시간 모니터링)**

```powershell
python -m schnitzel_stream `
  --camera-id cam01 `
  --visualize
```

**10) 프로덕션 실행**

```powershell
python -m schnitzel_stream --camera-id cam01
```

`--dry-run` 없이, `--max-events` 없이 — 연속 실행, 백엔드로 전송.

**11) 잘못된 조합 (에러 발생)**

```powershell
# --video + --source-type rtsp/plugin 조합은 불가
python -m schnitzel_stream --video test.mp4 --source-type rtsp    # 에러!
python -m schnitzel_stream --video test.mp4 --source-type plugin  # 에러!
```

---

2. Mock 백엔드 (`python -m ai.pipeline.mock_backend`)
------------------------------------------------------

`POST /api/events`를 수신하는 경량 HTTP 서버. 로컬 테스트용.

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MOCK_BACKEND_HOST` | `127.0.0.1` | 수신 호스트 |
| `MOCK_BACKEND_PORT` | `8080` | 수신 포트 |

### 사용법

**터미널 1 — mock 백엔드 시작:**

```powershell
python -m ai.pipeline.mock_backend
```

**터미널 2 — 파이프라인 실행 (mock으로 전송):**

```powershell
python -m schnitzel_stream --max-events 5
```

터미널 1 로그에 이벤트가 표시됨.

**커스텀 포트:**

```powershell
$env:MOCK_BACKEND_PORT = "18080"
python -m ai.pipeline.mock_backend
```

---

3. 멀티 카메라 (`python scripts/multi_cam.py`)
------------------------------------------------

`configs/cameras.yaml` 기반으로 카메라별 파이프라인 프로세스를 일괄 시작/종료.

### 명령어

```powershell
python scripts/multi_cam.py start                        # 활성 카메라 전부 시작
python scripts/multi_cam.py start --cameras cam01,cam02  # 특정 카메라만 시작
python scripts/multi_cam.py status                       # 실행 상태 확인
python scripts/multi_cam.py stop                         # 전부 종료
```

### 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--config`, `-c` | `configs/cameras.yaml` | 카메라 설정 파일 |
| `--log-dir`, `-l` | OS 임시 디렉터리 | 로그 및 PID 파일 디렉터리 |
| `--cameras` | 활성 전체 | 쉼표로 구분된 카메라 ID |
| `--extra-args` | 없음 | 파이프라인에 전달할 추가 인자 (예: `"--dry-run"`) |

### 예시: 전체 카메라 dry-run

```powershell
python scripts/multi_cam.py start --extra-args "--dry-run --max-events 10"
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

---

4. RTSP E2E 테스트 (`python scripts/check_rtsp.py`)
-----------------------------------------------------

자동화된 RTSP 안정성 테스트: MediaMTX + ffmpeg + mock 백엔드 + 파이프라인을 시작하고, 단절/재연결 시뮬레이션 후 복구를 검증.

**필수:** `ffmpeg`가 PATH에 등록되어 있어야 함. MediaMTX는 자동 다운로드.

### 사용법

```powershell
python scripts/check_rtsp.py                 # 테스트 실행
python scripts/check_rtsp.py --strict        # 복구 실패 시 에러 반환
python scripts/check_rtsp.py --log-dir C:\logs\rtsp_test
```

### 수행 과정

1. MediaMTX (RTSP 서버) 시작
2. Mock 백엔드 시작
3. ffmpeg로 비디오를 RTSP 스트림으로 송출
4. 파이프라인이 RTSP 소비 시작
5. 초기 이벤트 수신 대기
6. ffmpeg 종료 (단절 시뮬레이션)
7. ffmpeg 재시작
8. 파이프라인이 복구되어 새 이벤트를 전송하는지 검증

---

5. 회귀 테스트 (`python scripts/regression_check.py`)
------------------------------------------------------

샘플 비디오로 파이프라인을 실행하고, 골든 레퍼런스와 비교하여 회귀를 감지.
회귀 신호의 결정성을 위해 스크립트 내부에서 `AI_MODEL_MODE=mock`를 명시적으로 설정한다.

### 사용법

```powershell
# 골든 레퍼런스와 비교
python scripts/regression_check.py --max-events 5

# 골든 레퍼런스 업데이트 (의도적 변경 후)
python scripts/regression_check.py --max-events 5 --update-golden
```

결과: `regression_ok` 또는 `regression_failed` (차이점 상세 출력).

---

6. 정확도 평가 (`python scripts/accuracy_eval.py`)
----------------------------------------------------

정답 라벨 대비 모델 정확도를 평가. 실제 모델 어댑터 필요.

### 사용법

```powershell
python scripts/accuracy_eval.py ^
  --gt data/labels/ground_truth.jsonl ^
  --adapter "ai.vision.adapters.yolo_adapter:YOLOAdapter" ^
  --conf 0.25 --iou 0.5 ^
  --out metrics_summary.json
```

### 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--gt` | 필수 | 정답 JSONL 파일 |
| `--adapter` | 필수 | 모델 어댑터 (`모듈:클래스`) |
| `--class-map` | 없음 | 클래스 매핑 YAML |
| `--conf` | 0.25 | confidence 임계값 |
| `--iou` | 0.5 | IoU 임계값 |
| `--out` | `metrics_summary.json` | 결과 출력 파일 |

---

7. 테스트 (`pytest`)
-------------------------------

### 사용법

```text
# Windows PowerShell (세션당 1회)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"

# Linux/macOS
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# 전체 테스트 실행
pytest tests/ -v

# 카테고리별 실행
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/regression/ -v

# 특정 파일 실행
pytest tests/unit/pipeline/test_frame_processor.py -v

# 특정 테스트 함수 실행
pytest tests/unit/pipeline/test_frame_processor.py::test_processor_stop -v
```

### 테스트 위생 점검 (중복/무의미 테스트 탐지)

정적 위생 점검 도구로 다음을 탐지할 수 있습니다.

- 상수값만 다른 유사 중복 테스트 본문
- 검증 의도가 없는 테스트 (`assert`, `pytest.raises`, `assert*` 헬퍼 호출 없음)
- 의미가 약한 `assert True` 테스트

```text
# 크로스 플랫폼 (Windows/Linux/macOS)
python scripts/test_hygiene.py

# 엄격 모드 (임계치 초과 시 실패 코드 반환)
python scripts/test_hygiene.py --strict

# 기준선 게이트 (현재보다 나빠질 때만 실패)
python scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0

# JSON 리포트 저장
python scripts/test_hygiene.py --json-out outputs/test_hygiene_report.json
```

---

8. 환경 변수
--------------

### 코어 파이프라인 (`AI_*`)

| 변수 | 매핑 설정 | 기본값 | 설명 |
|------|----------|--------|------|
| `AI_EVENTS_POST_URL` | `events.post_url` | `http://localhost:8080/api/events` | 백엔드 URL |
| `AI_INGEST_FPS_LIMIT` | `ingest.fps_limit` | `10` | 프레임 레이트 제한 |
| `AI_SOURCE_TYPE` | `source.type` | `file` | `file`, `rtsp`, `webcam`, `plugin` |
| `AI_SOURCE_ADAPTER` | `source.adapter` | 없음 | Source 플러그인 경로 (`module:ClassName`, `AI_SOURCE_TYPE=plugin`과 함께 사용) |
| `AI_SENSOR_ENABLED` | `sensor.enabled` | `false` | 센서 축 스위치 (이벤트 `sensor` 필드에 최근 패킷 주입) |
| `AI_SENSOR_TYPE` | `sensor.type` | 없음 | 센서 타입 (`ros2`, `mqtt`, `modbus`, `serial`, `plugin`) |
| `AI_SENSOR_ADAPTER` | `sensor.adapter` | 없음 | 센서 플러그인 경로 (`module:ClassName`) |
| `AI_SENSOR_ADAPTERS` | `sensor.adapters` | 없음 | 다중 센서 어댑터 경로(콤마 구분, 예: `a:Front,b:Rear`) |
| `AI_SENSOR_TOPIC` | `sensor.topic` | 없음 | 센서 토픽/채널 힌트 |
| `AI_SENSOR_QUEUE_SIZE` | `sensor.queue_size` | `256` | 센서 큐 크기 |
| `AI_SENSOR_TIME_WINDOW_MS` | `sensor.time_window_ms` | `300` | 이벤트-센서 매칭 시간창(ms) |
| `AI_SENSOR_EMIT_EVENTS` | `sensor.emit_events` | `false` | 독립 `SENSOR_EVENT` 페이로드 전송 |
| `AI_SENSOR_EMIT_FUSED_EVENTS` | `sensor.emit_fused_events` | `false` | 추가 `FUSED_EVENT` 페이로드 전송 |
| `AI_FAKE_SENSOR_ID` | 플러그인 전용 | `ultrasonic-front-01` | fake 초음파 센서 ID |
| `AI_FAKE_SENSOR_INTERVAL_SEC` | 플러그인 전용 | `0.05` | fake 초음파 발행 주기(초) |
| `AI_MODEL_MODE` | `model.mode` | `real` | `real` 또는 `mock` (`mock`은 테스트 시 명시적으로만 사용) |
| `AI_MODEL_ADAPTER` | `model.adapter` | `ai.vision.adapters.custom_adapter:CustomModelAdapter` | 어댑터 경로 (기본 템플릿은 구현 전 fail-fast, 예: `ai.vision.adapters.yolo_adapter:YOLOAdapter`) |
| `AI_ZONES_SOURCE` | `zones.source` | `api` | `api`, `file`, `none` (`none`은 zone 평가 비활성) |
| `AI_RTSP_TRANSPORT` | `rtsp.transport` | `tcp` | `tcp` 또는 `udp` |
| `AI_RTSP_TIMEOUT_SEC` | `rtsp.timeout_sec` | `5.0` | 연결 타임아웃 |
| `AI_RTSP_MAX_ATTEMPTS` | `rtsp.max_attempts` | `0` (무제한) | 재연결 횟수 제한 |
| `AI_EVENTS_SNAPSHOT_BASE_DIR` | `events.snapshot.base_dir` | 없음 (비활성) | 스냅샷 저장 경로 |
| `AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX` | `events.snapshot.public_prefix` | 없음 | 스냅샷 URL prefix |
| `AI_EVENTS_EMITTER_ADAPTER` | `events.emitter_adapter` | 없음 | 커스텀 emitter 플러그인 경로 (`module:ClassName`) |
| `AI_ROS2_SOURCE_TOPIC` | 플러그인 전용 | `/camera/image_raw/compressed` | ROS2 source 토픽 |
| `AI_ROS2_SOURCE_MSG_TYPE` | 플러그인 전용 | `compressed` | `compressed` 또는 `image` |
| `AI_ROS2_SOURCE_NODE_NAME` | 플러그인 전용 | `ai_frame_source` | ROS2 source 노드 이름 |
| `AI_ROS2_SOURCE_QOS_DEPTH` | 플러그인 전용 | `10` | ROS2 source QoS depth |
| `AI_ROS2_SOURCE_READ_TIMEOUT_SEC` | 플러그인 전용 | `1.0` | source read timeout(초) |
| `AI_ROS2_SOURCE_FPS_HINT` | 플러그인 전용 | `0` | source FPS 힌트 |
| `AI_ROS2_EVENT_TOPIC` | 플러그인 전용 | `/ai/events` | ROS2 emitter 토픽 |
| `AI_ROS2_EMITTER_NODE_NAME` | 플러그인 전용 | `ai_event_emitter` | ROS2 emitter 노드 이름 |
| `AI_ROS2_EMITTER_QOS_DEPTH` | 플러그인 전용 | `100` | ROS2 emitter QoS depth |

### 로깅

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `AI_LOG_LEVEL` | `INFO` | 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `AI_LOG_FORMAT` | `plain` | `plain` 또는 `json` |
| `AI_LOG_MAX_BYTES` | `10485760` (10MB) | 로그 파일 최대 크기 (로테이션 기준) |
| `AI_LOG_BACKUP_COUNT` | `5` | 보관할 로테이션 로그 파일 수 |

### 모델 / 트래커 (어댑터 레벨)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `YOLO_MODEL_PATH` | 필수 | YOLO `.pt` 파일 경로 |
| `YOLO_CONF` | `0.25` | confidence 임계값 |
| `YOLO_DEVICE` | `auto` | `auto`, `cpu`, CUDA 장치 |
| `ONNX_MODEL_PATH` | 필수 | ONNX `.onnx` 파일 경로 |
| `ONNX_CONF` | `0.25` | confidence 임계값 |
| `ONNX_IOU` | `0.45` | NMS IoU 임계값 |
| `ONNX_PROVIDERS` | `CUDAExecutionProvider,CPUExecutionProvider` | 실행 프로바이더 |
| `MODEL_CLASS_MAP_PATH` | `configs/model_class_map.yaml` | 클래스-이벤트 매핑 |
| `TRACKER_TYPE` | `none` | `none`, `iou`, `bytetrack` |
| `TRACKER_MAX_AGE` | `30` | 미매칭 최대 프레임 수 |
| `TRACKER_MIN_HITS` | `1` | 트랙 시작 최소 감지 수 |
| `TRACKER_IOU` | `0.3` | 트래킹 IoU 임계값 |

---

9. 설정 파일
--------------

| 파일 | 용도 |
|------|------|
| `configs/default.yaml` | 기본 파이프라인 설정 |
| `configs/cameras.yaml` | 멀티 카메라 정의 (id, 소스 타입, URL/경로) |
| `configs/model_class_map.yaml` | 클래스 ID → 이벤트 타입 매핑 |
| `.env.example` | 모든 환경 변수 예시 |

### 설정 해석 순서

1. `configs/default.yaml` + `configs/cameras.yaml` 병합 (기본)
2. 런타임 프로필 오버레이 (`app.env` 기준 `configs/dev.yaml` 또는 `configs/prod.yaml`)
3. 환경 변수 오버라이드 (`AI_*`)
4. 실행 인자 기반 CLI/런타임 오버라이드 (`--graph`, `--camera-id`, `--video`, `--source-type`, `--camera-index`, `--validate-only`, `--report-json`, `--dry-run`, `--output-jsonl`, `--max-events`, `--visualize`, `--loop`)
