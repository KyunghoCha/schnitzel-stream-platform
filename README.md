# schnitzel-stream-platform

Edge-first universal stream processing platform.

- Stable entrypoint (SSOT): `python -m schnitzel_stream`
- Graph specs:
  - v1: job graph (legacy runtime indirection)
  - v2: node graph (in-proc DAG runtime)
- Core contracts (SSOT):
  - StreamPacket: `docs/contracts/stream_packet.md`
  - Observability (run report): `docs/contracts/observability.md`
- Execution plan SSOT: `docs/roadmap/execution_roadmap.md`

## Overview

### English

This repo is pivoting from a CCTV/video-specific pipeline into a **general-purpose stream platform**.

What you get today:

- One stable CLI entrypoint (`python -m schnitzel_stream`)
- v2 node graphs (YAML) executed in-process (strict DAG)
- Static graph validation (topology + compatibility)
- Edge-friendly durable queue building blocks (SQLite WAL)
- A preserved legacy video pipeline under `src/ai/` for compatibility/reference

### 한국어

이 레포는 CCTV/영상 파이프라인에서 출발했지만, 이제는 **범용 스트림 플랫폼**으로 피벗 중입니다.

현재 제공되는 것:

- 단일 안정 엔트리포인트(`python -m schnitzel_stream`)
- v2 node graph(YAML) in-proc 실행(엄격 DAG)
- 그래프 정적 검증(토폴로지 + 호환성)
- 엣지 친화 durable queue 빌딩블록(SQLite WAL)
- 호환/참조 목적의 레거시 영상 런타임(`src/ai/`) 유지

## Architecture

### Target Platform View (Ingress/Core/Egress/Meta)

```mermaid
flowchart LR
  subgraph Ingress[Ingress]
    S[Source Adapters]
    I[Interceptors]
  end

  subgraph Core[Core]
    G[Graph Runtime (v2 in-proc DAG)]
    N[Nodes (plugin boundary)]
  end

  subgraph Egress[Egress]
    Q[Durable Queue (SQLite/WAL)]
    R[Router/Policy]
    K[Sinks]
  end

  subgraph Meta[Meta]
    V[Validator]
    P[Plugin Policy]
    O[Observability]
  end

  S --> I --> G --> N --> Q --> R --> K

  V -. validate .-> G
  P -. allowlist .-> G
  O -. report .-> G
```

### Legacy Compatibility (v1 job graph)

v1 graphs exist to keep the migration reversible while the v2 platform evolves:

- v1 graph -> loads one job plugin -> executes legacy runtime
- default v1 graph: `configs/graphs/legacy_pipeline.yaml`

## Quickstart

### Prerequisites

- Python 3.11

### Install

```bash
pip install -r requirements.txt
```

### Environment

```powershell
# Windows (recommended)
./setup_env.ps1

# Linux/macOS
export PYTHONPATH=src
```

### Validate Graph (no run)

```bash
# default v1 graph
python -m schnitzel_stream validate

# explicit graph
python -m schnitzel_stream validate --graph configs/graphs/legacy_pipeline.yaml
```

### Run v2 In-Proc Demo Graph

```bash
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml

# JSON run report (metrics)
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --report-json
```

### Durable Queue Demo (SQLite WAL)

```bash
# enqueue
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml

# drain + ack
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
```

### Run Legacy Video Pipeline (v1) (Optional)

The legacy pipeline is executed through the v1 job graph and uses the Phase 0 CLI flags.

For a local smoke run without real model deps/backends, force mock mode:

```powershell
# PowerShell
$env:AI_MODEL_MODE="mock"
$env:AI_ZONES_SOURCE="none"
python -m schnitzel_stream --dry-run --max-events 5
```

## Graph Spec Formats

### v1 (job graph)

```yaml
version: 1
job: schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob
config: {}
```

### v2 (node graph)

- `plugin` must be `module:ClassName`
- `kind` is currently one of: `source`, `node`, `sink` (plus reserved: `delay`, `initial`)

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

## Contracts

- StreamPacket (node-to-node): `docs/contracts/stream_packet.md`
- Observability (run report JSON + metric naming): `docs/contracts/observability.md`

## Plugin Policy (Safety)

By default, plugin loading is allowlisted to repo namespaces (`schnitzel_stream.*`, `ai.*`).

- `ALLOWED_PLUGIN_PREFIXES` (comma-separated prefixes)
- `ALLOW_ALL_PLUGINS=true` (dev only)

## Cross-Platform (Edge-First)

- Canonical line endings: `.gitattributes` enforces LF.
- Deterministic paths: default graph path is resolved from repo root (not CWD).
- Packaging lanes (recommended):
  - Docker (prod)
  - venv (dev)

Support matrix (provisional): `docs/implementation/90-packaging/support_matrix.md`

## Documentation

Start here:

- `docs/index.md`

Key SSOT docs:

- `docs/roadmap/execution_roadmap.md`
- `docs/roadmap/strategic_roadmap.md`

## License

Apache 2.0. See `LICENSE`.
