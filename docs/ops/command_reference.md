# Command Reference

## English

Complete command reference for v2 node-graph runtime.

### Prerequisites

```powershell
# Windows
./setup_env.ps1
```

```bash
# Linux / macOS
export PYTHONPATH=src
```

Environment doctor:

```bash
python scripts/env_doctor.py
python scripts/env_doctor.py --strict --json
python scripts/env_doctor.py --profile yolo --json
python scripts/env_doctor.py --profile webcam --probe-webcam --camera-index 0
python scripts/env_doctor.py --profile console --strict --json
```

### Entrypoint

```bash
python -m schnitzel_stream [options]
python -m schnitzel_stream validate [--graph <path>]
```

Default graph: `configs/graphs/dev_vision_e2e_mock_v2.yaml`

### CLI Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--graph` | string | default v2 graph | Graph YAML path (`version: 2`) |
| `--validate-only` | flag | off | Validate and exit |
| `--report-json` | flag | off | Print JSON run report |
| `--max-events` | int | unlimited | Source packet budget |

### Common Commands

Validate graph:

```bash
python -m schnitzel_stream validate
python -m schnitzel_stream validate --graph configs/graphs/dev_inproc_demo_v2.yaml
```

Run graph:

```bash
python -m schnitzel_stream
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --report-json
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 100
```

### Preset Launcher (One-Command UX)

List presets:

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --list --experimental
```

Run presets:

```bash
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset webcam_frames --camera-index 0 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
python scripts/stream_run.py --preset file_yolo_view --experimental --model-path models/yolov8n.pt --device cpu --max-events 60
```

Options:
- `--validate-only`
- `--max-events <int>`
- `--input-path <path>` (file presets)
- `--camera-index <int>` (webcam presets)
- `--device <cpu|0|...>` (YOLO presets)
- `--model-path <path>` (YOLO presets)
- `--yolo-conf <float>` (YOLO presets)
- `--yolo-iou <float>` (YOLO presets)
- `--yolo-max-det <int>` (YOLO presets)
- `--loop <true|false>` (file presets)
- `--doctor` (run strict preflight checks before validate/run; exit code `3` on preflight failure)
- `--experimental` (required for `file_yolo_view`, `file_yolo_headless`, `webcam_yolo`)

### Graph Wizard (Template Profiles, Non-Interactive)

List available wizard profiles:

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --list-profiles --experimental
```

Generate + validate in one command:

```bash
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --profile file_frames --out configs/graphs/generated_file_frames_v2.yaml --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30 --validate-after-generate
python scripts/graph_wizard.py --profile file_yolo_headless --experimental --out configs/graphs/generated_file_yolo_headless_v2.yaml --model-path models/yolov8n.pt --device cpu
```

Validate an existing generated graph:

```bash
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

Exit codes:
- `0`: success
- `1`: runtime failure
- `2`: usage/input error
- `3`: precondition failure (experimental guard / validation failure)

### Demo Graphs

```bash
python -m schnitzel_stream --graph configs/graphs/dev_vision_e2e_mock_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_headless_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_stream_template_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

### Webcam YOLO + OpenCV Overlay

Install model dependencies (one-time):

```bash
pip install -r requirements-model.txt
pip install opencv-python
```

Run webcam detection with box overlay window:

```bash
python -m schnitzel_stream validate --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
```

Optional environment overrides:
- `SS_CAMERA_INDEX` (default: `0`)
- `SS_YOLO_MODEL_PATH` (default: `models/yolov8n.pt`)
- `SS_YOLO_CONF` (default: `0.35`)
- `SS_YOLO_IOU` (default: `0.45`)
- `SS_YOLO_DEVICE` (examples: `cpu`, `0`)
- `SS_WINDOW_NAME` (OpenCV window title)

Exit with `q`, `Q`, or `ESC` in the OpenCV window.

### File YOLO + OpenCV Overlay (Loop + Low-Latency)

```bash
export SS_INPUT_PATH=data/samples/2048246-hd_1920_1080_24fps.mp4
export SS_YOLO_MODEL_PATH=models/yolov8n.pt
export SS_YOLO_DEVICE=cpu   # use 0 for GPU
export SS_INPUT_LOOP=true

python -m schnitzel_stream validate --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
```

Notes:
- `dev_video_file_yolo_overlay_v2.yaml` sets `inbox_max=1` + `drop_oldest` on YOLO/display nodes.
- This keeps display latency low when inference is slower than source FPS.

### Demo Pack (Professor Showcase)

One-command profiles:

```bash
python scripts/demo_pack.py --profile ci
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

Options:
- `--profile <ci|professor>`
- `--camera-index <int>` (used for webcam showcase in professor profile)
- `--max-events <int>`
- `--report <path>` (default: `outputs/reports/demo_pack_latest.json`)

Report fields:
- `schema_version` (current: `2`)
- `scenarios[*].failure_kind` (`validate`, `run`, `environment`)
- `scenarios[*].failure_reason` (for example: `dependency_missing`, `webcam_runtime_failed`)

Render static summary from demo report:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format html --out-dir outputs/reports
```

Manual showcase scenarios:

```bash
# S1: in-proc baseline
python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_inproc_v2.yaml --max-events 50

# S2: durable enqueue + drain/ack
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_enqueue_v2.yaml
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_durable_enqueue_v2.yaml --max-events 50
python -m schnitzel_stream --graph configs/graphs/showcase_durable_drain_ack_v2.yaml --max-events 50

# S3: webcam
python -m schnitzel_stream validate --graph configs/graphs/showcase_webcam_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_webcam_v2.yaml --max-events 50
```

### Process Graph Foundation Validation

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

Exit codes:
- `0`: success
- `2`: spec/compat validation failure
- `1`: runtime/general failure

### Mock HTTP Backend (local sink test)

```bash
python -m schnitzel_stream.tools.mock_backend
```

Environment variables:
- `MOCK_BACKEND_HOST` (default: `127.0.0.1`)
- `MOCK_BACKEND_PORT` (default: `18080`)

### Utility Scripts

Environment doctor:

```bash
python scripts/env_doctor.py
python scripts/env_doctor.py --strict
python scripts/env_doctor.py --strict --json
python scripts/env_doctor.py --profile yolo --json
python scripts/env_doctor.py --profile yolo --model-path models/yolov8n.pt --strict --json
python scripts/env_doctor.py --profile webcam --probe-webcam --camera-index 0 --json
python scripts/env_doctor.py --profile console --strict --json
```

Environment doctor profiles:
- `base`: baseline runtime dependencies
- `yolo`: adds `ultralytics`/`torch`, CUDA visibility summary, optional model-path check
- `webcam`: optional camera-open probe (`--probe-webcam`)
- `console`: adds `fastapi`/`uvicorn` imports and `node`/`npm` executable checks

RTSP reconnect E2E (v2 graph):

```bash
python scripts/check_rtsp.py
python scripts/check_rtsp.py --strict
```

Regression helper (v2 golden):

```bash
python scripts/regression_check.py --max-events 5
python scripts/regression_check.py --max-events 5 --update-golden
```

Plugin scaffold:

```bash
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode
```

Scaffold export options:
- `--register-export` (default): update `packs/<pack>/nodes/__init__.py`
- `--no-register-export`: skip export registration

Stream fleet launcher (primary):

```bash
python scripts/stream_fleet.py start --graph-template configs/graphs/dev_stream_template_v2.yaml
python scripts/stream_fleet.py status
python scripts/stream_fleet.py stop
```

Preset launcher (one-command UX):

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
```

Graph wizard (template profile generation):

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

Read-only stream monitor (pid/log based):

```bash
python scripts/stream_monitor.py --log-dir /tmp/schnitzel_stream_fleet_run
python scripts/stream_monitor.py --once --json
```

One-command local console bootstrap:

```bash
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

Stream console options:
- `up --api-host --api-port --ui-host --ui-port --log-dir --allow-local-mutations --token --api-only --ui-only`
- `status --log-dir --json`
- `down --log-dir`
- `doctor --strict --json`

Process-graph validator:

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

Demo report renderer:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

Control policy snapshot drift checker:

```bash
python scripts/control_policy_snapshot.py
python scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json
```

Runtime environment variables used per stream process:
- `SS_STREAM_ID`
- `SS_INPUT_TYPE`
- `SS_INPUT_PLUGIN`
- `SS_INPUT_URL` (rtsp/plugin)
- `SS_INPUT_PATH` (file/plugin)
- `SS_INPUT_INDEX` (webcam/plugin)

Legacy key compatibility (accepted for one cycle):
- `SS_CAMERA_ID`
- `SS_SOURCE_TYPE`
- `SS_SOURCE_PLUGIN`
- `SS_SOURCE_URL`
- `SS_SOURCE_PATH`
- `SS_CAMERA_INDEX`

### Stream Control API (Local Operations Gateway)

Run server (default `127.0.0.1:18700`):

```bash
python scripts/stream_control_api.py
python scripts/stream_control_api.py --host 127.0.0.1 --port 18700 --audit-path outputs/audit/stream_control_audit.jsonl
```

Security mode:
- Default without token: local-only read access (`127.0.0.1`/`localhost`).
- Mutating endpoints require bearer by default in no-token mode:
  - `POST /api/v1/presets/{preset_id}/run`
  - `POST /api/v1/fleet/start`
  - `POST /api/v1/fleet/stop`
- Optional: set `SS_CONTROL_API_TOKEN` to require `Authorization: Bearer <token>` globally.
- One-cycle local override for mutating endpoints: `SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true`
- Audit retention defaults: `SS_AUDIT_MAX_BYTES=10485760`, `SS_AUDIT_MAX_FILES=5`
- CORS default allows local UI origins: `http://127.0.0.1:5173`, `http://localhost:5173`
- Override CORS origins: `SS_CONTROL_API_CORS_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"`

API surface (v1):
- `GET /api/v1/health`
- `GET /api/v1/presets?experimental=<bool>`
- `POST /api/v1/presets/{preset_id}/validate`
- `POST /api/v1/presets/{preset_id}/run`
- `POST /api/v1/fleet/start`
- `POST /api/v1/fleet/stop`
- `GET /api/v1/fleet/status`
- `GET /api/v1/monitor/snapshot`
- `POST /api/v1/env/check`
- `GET /api/v1/governance/policy-snapshot`
- `GET /api/v1/governance/audit?limit=<int>&since=<iso8601>`

Quick checks:

```bash
curl -s http://127.0.0.1:18700/api/v1/health
curl -s "http://127.0.0.1:18700/api/v1/presets?experimental=false"
curl -s -X POST http://127.0.0.1:18700/api/v1/env/check -H "Content-Type: application/json" -d '{"profile":"base","strict":false}'
```

### Stream Console Web UI (React + Vite + TypeScript)

```bash
cd apps/stream-console
npm ci
npm run dev
```

Other commands:
- `npm run typecheck`
- `npm run test`
- `npm run build`
- `npm run preview`

Semantics:
- Monitor tab data is fleet telemetry from pid/log streams.
- Preset run output is session-level result and does not create fleet monitor stream rows.

### Plugin Security Policy

Default allowlist: `schnitzel_stream.*`

Override (dev only):

```bash
export ALLOWED_PLUGIN_PREFIXES="schnitzel_stream.,my_org."
export ALLOW_ALL_PLUGINS=true
```

## 한국어

v2 노드 그래프 런타임 기준 명령어 레퍼런스입니다.

### 사전 준비

```powershell
# Windows
./setup_env.ps1
```

```bash
# Linux / macOS
export PYTHONPATH=src
```

환경 진단:

```bash
python scripts/env_doctor.py
python scripts/env_doctor.py --strict --json
python scripts/env_doctor.py --profile yolo --json
python scripts/env_doctor.py --profile webcam --probe-webcam --camera-index 0
python scripts/env_doctor.py --profile console --strict --json
```

### 엔트리포인트

```bash
python -m schnitzel_stream [options]
python -m schnitzel_stream validate [--graph <path>]
```

기본 그래프: `configs/graphs/dev_vision_e2e_mock_v2.yaml`

### CLI 옵션

| 옵션 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `--graph` | string | 기본 v2 그래프 | 그래프 YAML 경로 (`version: 2`) |
| `--validate-only` | flag | off | 검증 후 종료 |
| `--report-json` | flag | off | JSON 실행 리포트 출력 |
| `--max-events` | int | unlimited | 소스 패킷 예산 |

### 자주 쓰는 명령

검증:

```bash
python -m schnitzel_stream validate
python -m schnitzel_stream validate --graph configs/graphs/dev_inproc_demo_v2.yaml
```

실행:

```bash
python -m schnitzel_stream
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --report-json
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 100
```

### 프리셋 실행기(원커맨드 UX)

프리셋 목록:

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --list --experimental
```

프리셋 실행:

```bash
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset webcam_frames --camera-index 0 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
python scripts/stream_run.py --preset file_yolo_view --experimental --model-path models/yolov8n.pt --device cpu --max-events 60
```

옵션:
- `--validate-only`
- `--max-events <int>`
- `--input-path <path>` (file 프리셋)
- `--camera-index <int>` (webcam 프리셋)
- `--device <cpu|0|...>` (YOLO 프리셋)
- `--model-path <path>` (YOLO 프리셋)
- `--yolo-conf <float>` (YOLO 프리셋)
- `--yolo-iou <float>` (YOLO 프리셋)
- `--yolo-max-det <int>` (YOLO 프리셋)
- `--loop <true|false>` (file 프리셋)
- `--doctor` (실행 전 strict 사전 진단; preflight 실패 시 종료 코드 `3`)
- `--experimental` (`file_yolo_view`, `file_yolo_headless`, `webcam_yolo` 실행 시 필수)

### Graph Wizard(템플릿 프로필, 비상호작용)

사용 가능한 wizard 프로필 목록:

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --list-profiles --experimental
```

생성 + 검증 원커맨드:

```bash
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --profile file_frames --out configs/graphs/generated_file_frames_v2.yaml --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30 --validate-after-generate
python scripts/graph_wizard.py --profile file_yolo_headless --experimental --out configs/graphs/generated_file_yolo_headless_v2.yaml --model-path models/yolov8n.pt --device cpu
```

생성된 그래프 단독 검증:

```bash
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

종료 코드:
- `0`: 성공
- `1`: 런타임 실패
- `2`: 사용법/입력 오류
- `3`: 사전조건 실패(experimental 가드 / 검증 실패)

### 데모 그래프

```bash
python -m schnitzel_stream --graph configs/graphs/dev_vision_e2e_mock_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_headless_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_stream_template_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

### 웹캠 YOLO + OpenCV 오버레이

모델 의존성 설치(최초 1회):

```bash
pip install -r requirements-model.txt
pip install opencv-python
```

웹캠 사람/객체 검출 + 박스 오버레이 창 실행:

```bash
python -m schnitzel_stream validate --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_yolo_overlay_v2.yaml
```

선택 환경변수:
- `SS_CAMERA_INDEX` (기본: `0`)
- `SS_YOLO_MODEL_PATH` (기본: `models/yolov8n.pt`)
- `SS_YOLO_CONF` (기본: `0.35`)
- `SS_YOLO_IOU` (기본: `0.45`)
- `SS_YOLO_DEVICE` (예: `cpu`, `0`)
- `SS_WINDOW_NAME` (OpenCV 창 제목)

OpenCV 창에서 `q`, `Q`, `ESC` 키로 종료할 수 있습니다.

### 파일 YOLO + OpenCV 오버레이 (반복 재생 + 저지연)

```bash
export SS_INPUT_PATH=data/samples/2048246-hd_1920_1080_24fps.mp4
export SS_YOLO_MODEL_PATH=models/yolov8n.pt
export SS_YOLO_DEVICE=cpu   # GPU는 0 사용
export SS_INPUT_LOOP=true

python -m schnitzel_stream validate --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
```

참고:
- `dev_video_file_yolo_overlay_v2.yaml`은 YOLO/display 노드에 `inbox_max=1` + `drop_oldest`를 설정한다.
- 추론이 입력 FPS보다 느릴 때 화면 지연 누적을 줄이기 위한 정책이다.

### 데모 팩(교수님 시연)

원커맨드 프로필:

```bash
python scripts/demo_pack.py --profile ci
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

옵션:
- `--profile <ci|professor>`
- `--camera-index <int>` (professor 프로필의 웹캠 시나리오 인덱스)
- `--max-events <int>`
- `--report <path>` (기본: `outputs/reports/demo_pack_latest.json`)

리포트 필드:
- `schema_version` (현재: `2`)
- `scenarios[*].failure_kind` (`validate`, `run`, `environment`)
- `scenarios[*].failure_reason` (예: `dependency_missing`, `webcam_runtime_failed`)

데모 리포트 정적 요약 생성:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format html --out-dir outputs/reports
```

수동 시연 시나리오:

```bash
# S1: in-proc 기본선
python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_inproc_v2.yaml --max-events 50

# S2: durable enqueue + drain/ack
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_enqueue_v2.yaml
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_durable_enqueue_v2.yaml --max-events 50
python -m schnitzel_stream --graph configs/graphs/showcase_durable_drain_ack_v2.yaml --max-events 50

# S3: 웹캠
python -m schnitzel_stream validate --graph configs/graphs/showcase_webcam_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_webcam_v2.yaml --max-events 50
```

### 프로세스 그래프 Foundation 검증

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

종료 코드:
- `0`: 성공
- `2`: 스펙/호환성 검증 실패
- `1`: 런타임/일반 오류

### Mock HTTP 백엔드(로컬 싱크 테스트)

```bash
python -m schnitzel_stream.tools.mock_backend
```

환경변수:
- `MOCK_BACKEND_HOST` (기본: `127.0.0.1`)
- `MOCK_BACKEND_PORT` (기본: `18080`)

### 유틸리티 스크립트

환경 진단:

```bash
python scripts/env_doctor.py
python scripts/env_doctor.py --strict
python scripts/env_doctor.py --strict --json
python scripts/env_doctor.py --profile yolo --json
python scripts/env_doctor.py --profile yolo --model-path models/yolov8n.pt --strict --json
python scripts/env_doctor.py --profile webcam --probe-webcam --camera-index 0 --json
python scripts/env_doctor.py --profile console --strict --json
```

env_doctor 프로필:
- `base`: 기본 런타임 의존성 검사
- `yolo`: `ultralytics`/`torch`, CUDA 가시성 요약, 모델 경로(선택) 점검
- `webcam`: 카메라 오픈 프로브(옵션, `--probe-webcam`)
- `console`: `fastapi`/`uvicorn` import와 `node`/`npm` 실행파일 점검

RTSP 재연결 E2E(v2 그래프):

```bash
python scripts/check_rtsp.py
python scripts/check_rtsp.py --strict
```

회귀 헬퍼(v2 golden):

```bash
python scripts/regression_check.py --max-events 5
python scripts/regression_check.py --max-events 5 --update-golden
```

플러그인 스캐폴드:

```bash
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode
```

스캐폴드 export 옵션:
- `--register-export` (기본): `packs/<pack>/nodes/__init__.py` 자동 갱신
- `--no-register-export`: export 등록 생략

Stream fleet 실행기(주 경로):

```bash
python scripts/stream_fleet.py start --graph-template configs/graphs/dev_stream_template_v2.yaml
python scripts/stream_fleet.py status
python scripts/stream_fleet.py stop
```

프리셋 실행기(원커맨드 UX):

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
```

Graph wizard(템플릿 프로필 생성):

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

읽기 전용 stream 모니터(pid/log 기반):

```bash
python scripts/stream_monitor.py --log-dir /tmp/schnitzel_stream_fleet_run
python scripts/stream_monitor.py --once --json
```

원커맨드 로컬 콘솔 부트스트랩:

```bash
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

stream_console 옵션:
- `up --api-host --api-port --ui-host --ui-port --log-dir --allow-local-mutations --token --api-only --ui-only`
- `status --log-dir --json`
- `down --log-dir`
- `doctor --strict --json`

프로세스 그래프 검증기:

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

데모 리포트 렌더러:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

stream별 런타임 환경변수:
- `SS_STREAM_ID`
- `SS_INPUT_TYPE`
- `SS_INPUT_PLUGIN`
- `SS_INPUT_URL` (rtsp/plugin)
- `SS_INPUT_PATH` (file/plugin)
- `SS_INPUT_INDEX` (webcam/plugin)

레거시 키 호환(1사이클 허용):
- `SS_CAMERA_ID`
- `SS_SOURCE_TYPE`
- `SS_SOURCE_PLUGIN`
- `SS_SOURCE_URL`
- `SS_SOURCE_PATH`
- `SS_CAMERA_INDEX`

### Stream Control API (로컬 운영 게이트웨이)

서버 실행(기본 `127.0.0.1:18700`):

```bash
python scripts/stream_control_api.py
python scripts/stream_control_api.py --host 127.0.0.1 --port 18700 --audit-path outputs/audit/stream_control_audit.jsonl
```

보안 모드:
- 토큰이 없으면 기본은 로컬 read-only 접근(`127.0.0.1`/`localhost`)
- no-token 모드에서 mutating endpoint는 기본적으로 Bearer 필요:
  - `POST /api/v1/presets/{preset_id}/run`
  - `POST /api/v1/fleet/start`
  - `POST /api/v1/fleet/stop`
- 옵션: `SS_CONTROL_API_TOKEN` 설정 시 전체 endpoint에 `Authorization: Bearer <token>` 필수
- 1사이클 임시 로컬 완화: `SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true`
- 감사 보존 기본값: `SS_AUDIT_MAX_BYTES=10485760`, `SS_AUDIT_MAX_FILES=5`
- 기본 CORS 허용 origin: `http://127.0.0.1:5173`, `http://localhost:5173`
- CORS 커스텀: `SS_CONTROL_API_CORS_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"`

API 표면(v1):
- `GET /api/v1/health`
- `GET /api/v1/presets?experimental=<bool>`
- `POST /api/v1/presets/{preset_id}/validate`
- `POST /api/v1/presets/{preset_id}/run`
- `POST /api/v1/fleet/start`
- `POST /api/v1/fleet/stop`
- `GET /api/v1/fleet/status`
- `GET /api/v1/monitor/snapshot`
- `POST /api/v1/env/check`
- `GET /api/v1/governance/policy-snapshot`
- `GET /api/v1/governance/audit?limit=<int>&since=<iso8601>`

빠른 확인:

```bash
curl -s http://127.0.0.1:18700/api/v1/health
curl -s "http://127.0.0.1:18700/api/v1/presets?experimental=false"
curl -s -X POST http://127.0.0.1:18700/api/v1/env/check -H "Content-Type: application/json" -d '{"profile":"base","strict":false}'
```

### Stream Console 웹 UI (React + Vite + TypeScript)

```bash
cd apps/stream-console
npm ci
npm run dev
```

추가 명령:
- `npm run typecheck`
- `npm run test`
- `npm run build`
- `npm run preview`

의미:
- Monitor 탭 데이터는 fleet pid/log 기반 telemetry다.
- Preset run 결과는 session 단위 출력이며 fleet monitor stream row를 만들지 않는다.

### 플러그인 보안 정책

기본 allowlist: `schnitzel_stream.*`

개발 환경 override:

```bash
export ALLOWED_PLUGIN_PREFIXES="schnitzel_stream.,my_org."
export ALLOW_ALL_PLUGINS=true
```
