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

### Demo Graphs

```bash
python -m schnitzel_stream --graph configs/graphs/dev_vision_e2e_mock_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

### Mock HTTP Backend (local sink test)

```bash
python -m schnitzel_stream.tools.mock_backend
```

Environment variables:
- `MOCK_BACKEND_HOST` (default: `127.0.0.1`)
- `MOCK_BACKEND_PORT` (default: `18080`)

### Utility Scripts

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

Multi-camera graph launcher:

```bash
python scripts/multi_cam.py start --graph-template configs/graphs/dev_camera_template_v2.yaml
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

Runtime environment variables used per camera process:
- `SS_CAMERA_ID`
- `SS_SOURCE_TYPE`
- `SS_SOURCE_PLUGIN`
- `SS_SOURCE_URL` (rtsp/plugin)
- `SS_SOURCE_PATH` (file/plugin)
- `SS_CAMERA_INDEX` (webcam/plugin)

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

### 데모 그래프

```bash
python -m schnitzel_stream --graph configs/graphs/dev_vision_e2e_mock_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

### Mock HTTP 백엔드(로컬 싱크 테스트)

```bash
python -m schnitzel_stream.tools.mock_backend
```

환경변수:
- `MOCK_BACKEND_HOST` (기본: `127.0.0.1`)
- `MOCK_BACKEND_PORT` (기본: `18080`)

### 유틸리티 스크립트

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

멀티 카메라 그래프 런처:

```bash
python scripts/multi_cam.py start --graph-template configs/graphs/dev_camera_template_v2.yaml
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

카메라별 런타임 환경변수:
- `SS_CAMERA_ID`
- `SS_SOURCE_TYPE`
- `SS_SOURCE_PLUGIN`
- `SS_SOURCE_URL` (rtsp/plugin)
- `SS_SOURCE_PATH` (file/plugin)
- `SS_CAMERA_INDEX` (webcam/plugin)

### 플러그인 보안 정책

기본 allowlist: `schnitzel_stream.*`

개발 환경 override:

```bash
export ALLOWED_PLUGIN_PREFIXES="schnitzel_stream.,my_org."
export ALLOW_ALL_PLUGINS=true
```
