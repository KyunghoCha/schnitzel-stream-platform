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
python -m schnitzel_stream --graph configs/graphs/dev_camera_template_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

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
```

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

Multi-camera graph launcher:

```bash
python scripts/multi_cam.py start --graph-template configs/graphs/dev_camera_template_v2.yaml
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

Process-graph validator:

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

Demo report renderer:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
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

환경 진단:

```bash
python scripts/env_doctor.py
python scripts/env_doctor.py --strict --json
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
python -m schnitzel_stream --graph configs/graphs/dev_camera_template_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_json_file_sink_v2.yaml
```

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
```

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

멀티 카메라 그래프 런처:

```bash
python scripts/multi_cam.py start --graph-template configs/graphs/dev_camera_template_v2.yaml
python scripts/multi_cam.py status
python scripts/multi_cam.py stop
```

프로세스 그래프 검증기:

```bash
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml
python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml --report-json
```

데모 리포트 렌더러:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
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
