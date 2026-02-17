# schnitzel-stream-platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Status](https://img.shields.io/badge/Status-Active-informational)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

> Edge-first universal stream processing platform
> 엣지 우선 범용 스트림 플랫폼

Stable entrypoint (SSOT): `python -m schnitzel_stream`

---

## English

### Overview

`schnitzel-stream-platform` is a v2 node-graph runtime for stream processing.

Current focus:
- portable node graph execution (`version: 2`)
- strict graph validation (topology + compatibility)
- plugin-based IO/policy nodes
- durable queue primitives (SQLite/WAL)
- edge-oriented ops conventions
- CLI is graph-native only

### Architecture

```mermaid
flowchart LR
  subgraph Ingress["Ingress"]
    S["Source Plugins"]
  end

  subgraph Runtime["Runtime"]
    V["Graph Validator"]
    G["In-Proc Scheduler"]
    N["Node Plugins"]
  end

  subgraph Egress["Egress"]
    D["Durable Queue Nodes"]
    K["Sink Plugins"]
  end

  subgraph Meta["Meta"]
    P["Plugin Policy Allowlist"]
    O["Observability Contract"]
  end

  S --> G --> N --> D --> K
  V -."validate".-> G
  P -."govern".-> G
  O -."report".-> G
```

### Quickstart

1. Bootstrap (zero-env-first)

```powershell
# Windows PowerShell
./setup_env.ps1 -Profile console -Manager pip -SkipDoctor
```

```bash
# Linux/macOS
./setup_env.sh --profile console --manager pip --skip-doctor
```

2. Doctor

```bash
python scripts/stream_console.py doctor --strict --json
```

3. Up / Down

```bash
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

4. Validate runtime graph

```bash
python -m schnitzel_stream validate
```

5. Run default v2 graph

```bash
python -m schnitzel_stream
```

6. Useful demo graphs

```bash
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
```

6-1. File YOLO overlay (loop + low-latency queue policy)

```bash
export SS_INPUT_PATH=data/samples/2048246-hd_1920_1080_24fps.mp4
export SS_YOLO_MODEL_PATH=models/yolov8n.pt
export SS_YOLO_DEVICE=cpu   # use 0 for GPU
export SS_INPUT_LOOP=true
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
```

7. One-command demo pack (showcase profiles)

```bash
python scripts/demo_pack.py --profile ci
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

- Default report path: `outputs/reports/demo_pack_latest.json`
- Manual fallback guide: `docs/guides/professor_showcase_guide.md`

8. Render static report summary (no GUI required)

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

9. Stream fleet operations (universal runner + monitor)

```bash
python scripts/stream_fleet.py start --graph-template configs/graphs/dev_stream_template_v2.yaml
python scripts/stream_fleet.py status
python scripts/stream_monitor.py --once --json
python scripts/stream_fleet.py stop
```

10. One-command preset launcher

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
python scripts/stream_run.py --preset file_yolo_view --experimental --model-path models/yolov8n.pt --device cpu --max-events 60
```

- Default path is option-first (no env required); env vars remain as advanced overrides.

10-1. Graph wizard (template profile generation, non-interactive)

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

- Use `--experimental` for opt-in profiles (`file_yolo_headless`, `file_yolo_view`, `webcam_yolo`).
- Detailed guide: `docs/guides/graph_wizard_guide.md`

11. Control API server (local-first, optional bearer token)

```bash
# recommended: set bearer token for all control calls
export SS_CONTROL_API_TOKEN=change-me

python scripts/stream_control_api.py --host 127.0.0.1 --port 18700
```

- In local-only mode without token, mutating endpoints are blocked by default:
  - `POST /api/v1/presets/{preset_id}/run`
  - `POST /api/v1/fleet/start`
  - `POST /api/v1/fleet/stop`
- Temporary one-cycle local override: `SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true`
- Audit retention defaults: `SS_AUDIT_MAX_BYTES=10485760`, `SS_AUDIT_MAX_FILES=5`
- Policy snapshot drift gate: `python scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json`

12. Thin web console (React + Vite + TypeScript)

```bash
cd apps/stream-console
npm ci
npm run dev
```

- Monitor tab is fleet-only telemetry (PID/log based).
- Preset run output is session output and is not counted as fleet monitor stream rows.

13. One-command local console bootstrap (doctor -> up -> status -> down)

```bash
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

- `--allow-local-mutations` is explicit local-lab opt-in for mutating endpoints.
- Use `--token <value>` on `up` to set API bearer mode from bootstrap command.
- Detailed guide: `docs/guides/local_console_quickstart.md`

14. Block editor MVP (GUI graph authoring)

```bash
python scripts/stream_console.py up --allow-local-mutations
# open http://127.0.0.1:5173 and go to the "Editor" tab
```

- Supports: node placement/link/property editing, YAML import/export, validate/run.
- Direct manipulation: drag nodes on canvas and connect edges via handles.
- Built-in layout actions: `Auto Layout`, `Align Horizontal`, `Align Vertical`, `Fit View`.
- Validation view: status badge (`ok/error`), node/edge counts, readable failure summary.
- Compatibility: manual Add Edge form is still kept for one cycle.
- Detailed guide: `docs/guides/block_editor_quickstart.md`

### Graph Spec (v2)

- `plugin` format: `module:ClassName`
- node `kind`: `source`, `node`, `sink` (reserved: `delay`, `initial`)

```yaml
version: 2
nodes:
  - id: src
    kind: source
    plugin: schnitzel_stream.nodes.dev:StaticSource
    config:
      packets: []
  - id: out
    kind: sink
    plugin: schnitzel_stream.nodes.dev:PrintSink
edges:
  - from: src
    to: out
config: {}
```

### Node Kind Model (5 kinds)

```mermaid
flowchart LR
  I["initial<br/>bootstrap packet/state"] --> N1["node<br/>process(packet)"]
  S["source<br/>run()"] --> N1
  N1 --> D["delay<br/>gated pass-through"]
  D --> N2["node<br/>process(packet)"]
  N2 --> K["sink<br/>terminal process(packet)"]
```

- `source`: emits packets through `run()`; must not have incoming edges.
- `node`: generic transform/router; can be used for fan-in/fan-out.
- `sink`: terminal consumer; must not have outgoing edges.
- `delay`: time/condition-gated pass-through kind; currently handled via plugin `process()` semantics.
- `initial`: bootstrap kind for initial state/seed packet injection at graph start.

Runtime note:
- In the current in-proc runtime, only `source` has dedicated scheduler behavior.
- `node`, `sink`, `delay`, `initial` are executed via `process()` once packets are enqueued.

### Plugin Policy

Default allowlist is `schnitzel_stream.*`.

- `ALLOWED_PLUGIN_PREFIXES` (comma-separated prefixes)
- `ALLOW_ALL_PLUGINS=true` (dev only)

### Documentation

- Docs index: `docs/index.md`
- Documentation inventory: `docs/reference/document_inventory.md`
- Documentation policy: `docs/governance/documentation_policy.md`
- Doc-code mapping: `docs/reference/doc_code_mapping.md`
- Progress index: `docs/progress/README.md`
- Current status snapshot: `docs/progress/current_status.md`
- Execution SSOT: `docs/roadmap/execution_roadmap.md`
- StreamPacket contract: `docs/contracts/stream_packet.md`
- Observability contract: `docs/contracts/observability.md`

---

## 한국어

### 개요

`schnitzel-stream-platform`은 v2 노드 그래프 기반 스트림 처리 런타임입니다.

현재 핵심:
- `version: 2` 노드 그래프 실행
- 그래프 정적 검증(토폴로지 + 호환성)
- 플러그인 기반 입출력/정책 노드
- 내구 큐(SQLite/WAL) 빌딩블록
- 엣지 운영 관례 정리
- CLI는 그래프 중심 인터페이스만 지원

### 아키텍처

```mermaid
flowchart LR
  subgraph Ingress["Ingress"]
    S["입력 소스 플러그인"]
  end

  subgraph Runtime["Runtime"]
    V["그래프 검증기"]
    G["인프로세스 스케줄러"]
    N["노드 플러그인"]
  end

  subgraph Egress["Egress"]
    D["내구 큐 노드"]
    K["출력 싱크 플러그인"]
  end

  subgraph Meta["Meta"]
    P["플러그인 Allowlist 정책"]
    O["관측 가능성 계약"]
  end

  S --> G --> N --> D --> K
  V -."검증".-> G
  P -."정책".-> G
  O -."리포트".-> G
```

### 빠른 시작

1. Bootstrap (무환경변수 우선)

```powershell
# Windows PowerShell
./setup_env.ps1 -Profile console -Manager pip -SkipDoctor
```

```bash
# Linux/macOS
./setup_env.sh --profile console --manager pip --skip-doctor
```

2. Doctor

```bash
python scripts/stream_console.py doctor --strict --json
```

3. Up / Down

```bash
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

4. 런타임 그래프 검증

```bash
python -m schnitzel_stream validate
```

5. 기본 v2 그래프 실행

```bash
python -m schnitzel_stream
```

6. 주요 데모 그래프

```bash
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_rtsp_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_webcam_frames_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_http_event_sink_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_jsonl_sink_v2.yaml
```

6-1. 파일 YOLO 오버레이(반복 재생 + 저지연 큐 정책)

```bash
export SS_INPUT_PATH=data/samples/2048246-hd_1920_1080_24fps.mp4
export SS_YOLO_MODEL_PATH=models/yolov8n.pt
export SS_YOLO_DEVICE=cpu   # GPU는 0 사용
export SS_INPUT_LOOP=true
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay_v2.yaml
```

7. 원커맨드 데모 팩(쇼케이스 프로필)

```bash
python scripts/demo_pack.py --profile ci
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

- 기본 리포트 경로: `outputs/reports/demo_pack_latest.json`
- 수동 시연 fallback 가이드: `docs/guides/professor_showcase_guide.md`

8. 정적 리포트 요약 생성(GUI 없이 확인)

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

9. Stream fleet 운영(범용 실행기 + 모니터)

```bash
python scripts/stream_fleet.py start --graph-template configs/graphs/dev_stream_template_v2.yaml
python scripts/stream_fleet.py status
python scripts/stream_monitor.py --once --json
python scripts/stream_fleet.py stop
```

10. 원커맨드 프리셋 실행기

```bash
python scripts/stream_run.py --list
python scripts/stream_run.py --preset inproc_demo --validate-only
python scripts/stream_run.py --preset file_frames --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30
python scripts/stream_run.py --preset file_yolo_headless --experimental --doctor --validate-only
python scripts/stream_run.py --preset file_yolo_view --experimental --model-path models/yolov8n.pt --device cpu --max-events 60
```

- 기본 경로는 옵션 중심(no env)이며, 환경변수 방식은 고급 override 용도로 유지한다.

10-1. Graph wizard(템플릿 프로필 생성, 비상호작용)

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python scripts/graph_wizard.py --validate --spec configs/graphs/generated_inproc_demo_v2.yaml
```

- 실험 프로필(`file_yolo_headless`, `file_yolo_view`, `webcam_yolo`)은 `--experimental`로 opt-in 한다.
- 상세 가이드: `docs/guides/graph_wizard_guide.md`

11. Control API 서버(로컬 기본, 선택적 Bearer 토큰)

```bash
# 권장: 제어 호출 전체에 Bearer 토큰 사용
export SS_CONTROL_API_TOKEN=change-me

python scripts/stream_control_api.py --host 127.0.0.1 --port 18700
```

- 토큰 없이 local-only 모드일 때 mutating endpoint는 기본 차단:
  - `POST /api/v1/presets/{preset_id}/run`
  - `POST /api/v1/fleet/start`
  - `POST /api/v1/fleet/stop`
- 임시(1사이클) 로컬 완화: `SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true`
- 감사 보존 기본값: `SS_AUDIT_MAX_BYTES=10485760`, `SS_AUDIT_MAX_FILES=5`
- 정책 스냅샷 드리프트 게이트: `python scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json`

12. Thin Web 콘솔(React + Vite + TypeScript)

```bash
cd apps/stream-console
npm ci
npm run dev
```

- Monitor 탭은 fleet 로그/PID 기반 telemetry만 보여준다.
- Preset run 결과는 session output이며 fleet monitor stream row로 집계되지 않는다.

13. 원커맨드 로컬 콘솔 부트스트랩(doctor -> up -> status -> down)

```bash
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

- `--allow-local-mutations`는 로컬 실습 환경에서만 mutating endpoint를 명시적으로 여는 옵션이다.
- `up`에서 `--token <value>`를 주면 API를 bearer 모드로 바로 띄울 수 있다.
- 상세 가이드: `docs/guides/local_console_quickstart.md`

14. 블록 에디터 MVP(GUI 그래프 작성)

```bash
python scripts/stream_console.py up --allow-local-mutations
# http://127.0.0.1:5173 접속 후 "Editor" 탭 이동
```

- 지원 범위: 노드 배치/연결/속성 편집, YAML import/export, validate/run
- 직접 조작: 캔버스에서 노드를 드래그하고 핸들 연결로 엣지를 생성
- 내장 정렬 액션: `Auto Layout`, `Align Horizontal`, `Align Vertical`, `Fit View`
- 검증 표시: 상태 배지(`ok/error`), 노드/엣지 수, 읽기 쉬운 실패 요약
- 호환성: 수동 Add Edge 폼은 1사이클 동안 유지
- 상세 가이드: `docs/guides/block_editor_quickstart.md`

### 그래프 스펙(v2)

- `plugin` 형식: `module:ClassName`
- 노드 `kind`: `source`, `node`, `sink` (예약: `delay`, `initial`)

```yaml
version: 2
nodes:
  - id: src
    kind: source
    plugin: schnitzel_stream.nodes.dev:StaticSource
    config:
      packets: []
  - id: out
    kind: sink
    plugin: schnitzel_stream.nodes.dev:PrintSink
edges:
  - from: src
    to: out
config: {}
```

### 노드 Kind 모델(5종)

```mermaid
flowchart LR
  I["initial<br/>초기 패킷/상태 주입"] --> N1["node<br/>process(packet)"]
  S["source<br/>run()"] --> N1
  N1 --> D["delay<br/>조건/시간 기반 통과"]
  D --> N2["node<br/>process(packet)"]
  N2 --> K["sink<br/>종단 process(packet)"]
```

- `source`: `run()`으로 패킷을 생성하는 시작 노드이며 incoming edge를 가질 수 없습니다.
- `node`: 일반 변환/라우팅 노드이며 fan-in, fan-out 구성의 중심이 됩니다.
- `sink`: 최종 소비 노드이며 outgoing edge를 가질 수 없습니다.
- `delay`: 시간/조건 기반으로 패킷 흐름을 제어하는 kind이며 현재는 플러그인 `process()` 의미로 동작합니다.
- `initial`: 그래프 시작 시 초기 상태/시드 패킷을 주입할 때 쓰는 kind입니다.

런타임 참고:
- 현재 in-proc 런타임에서 스케줄러 특수 경로를 가지는 건 `source`입니다.
- `node`, `sink`, `delay`, `initial`은 큐에 들어온 패킷을 `process()`로 처리합니다.

### 플러그인 정책

기본 allowlist는 `schnitzel_stream.*` 입니다.

- `ALLOWED_PLUGIN_PREFIXES` (콤마 구분 prefix)
- `ALLOW_ALL_PLUGINS=true` (개발용)

### 문서

- 문서 인덱스: `docs/index.md`
- 문서 인벤토리: `docs/reference/document_inventory.md`
- 문서 정책: `docs/governance/documentation_policy.md`
- 문서-코드 매핑: `docs/reference/doc_code_mapping.md`
- 진행 인덱스: `docs/progress/README.md`
- 현재 상태 스냅샷: `docs/progress/current_status.md`
- 실행 SSOT: `docs/roadmap/execution_roadmap.md`
- StreamPacket 계약: `docs/contracts/stream_packet.md`
- 관측 가능성 계약: `docs/contracts/observability.md`

---

### License

Apache License 2.0 (`LICENSE`)

---

<p align="center">
  Made with ❤️ by <b>Kyungho Cha</b>
</p>
