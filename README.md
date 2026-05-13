# schnitzel-stream-platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Status](https://img.shields.io/badge/Status-Active-informational)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

Edge-first stream processing runtime built around validated node graphs and plugin-based sources, processors, and sinks.

Stable entrypoint:

```bash
python -m schnitzel_stream
```

## What This Repository Provides

- A node graph runtime for portable stream processing.
- Strict graph validation for topology and plugin compatibility.
- Plugin boundaries for `source`, `node`, and `sink` components.
- Durable queue primitives based on SQLite/WAL.
- Local operations tools for presets, fleet processes, monitoring, and a thin web console.
- Release and CI gates for command-surface, policy, documentation, and environment drift.

## Quickstart

### 1. Bootstrap

Windows PowerShell:

```powershell
./setup_env.ps1 -Profile console -Manager pip -SkipDoctor
```

Linux/macOS:

```bash
./setup_env.sh --profile console --manager pip --skip-doctor
```

### 2. Check The Environment

```bash
python scripts/stream_console.py doctor --strict --json
```

### 3. Validate And Run A Graph

```bash
python -m schnitzel_stream validate
python -m schnitzel_stream
```

Run a specific graph:

```bash
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack.yaml
python -m schnitzel_stream --graph configs/graphs/dev_video_file_yolo_overlay.yaml
```

### 4. Run The Demo Pack

```bash
python scripts/demo_pack.py --profile ci
python scripts/demo_pack.py --profile webcam --camera-index 0 --max-events 50
```

Default report:

```text
outputs/reports/demo_pack_latest.json
```

Manual guide:

```text
docs/guides/demo_pack_guide.md
```

### 5. Start The Local Console

```bash
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

Then open:

```text
http://127.0.0.1:5173
```

The console supports preset runs, fleet monitoring, and GUI graph authoring.

## Node Graph Format

Node graph specs are identified by the `nodes` and `edges` envelope. Do not add a graph `version` field.

```yaml
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

Supported node kinds:

- `source`: emits stream packets.
- `node`: transforms or routes packets.
- `sink`: consumes terminal packets.
- `delay`: reserved pass-through timing/condition kind.
- `initial`: reserved bootstrap state/seed kind.

Only `source` has special scheduler behavior in the current in-process runtime. Other kinds run through plugin `process()` semantics after packets are enqueued.

## Common Commands

| Task | Command |
| --- | --- |
| Validate default graph | `python -m schnitzel_stream validate` |
| Run default graph | `python -m schnitzel_stream` |
| List presets | `python scripts/stream_run.py --list` |
| Run a preset validation | `python scripts/stream_run.py --preset inproc_demo --validate-only` |
| Generate a graph from a profile | `python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo.yaml --validate-after-generate` |
| Start fleet processes | `python scripts/stream_fleet.py start --graph-template configs/graphs/dev_stream_template.yaml` |
| Inspect fleet status | `python scripts/stream_fleet.py status` |
| Monitor once | `python scripts/stream_monitor.py --once --json` |
| Stop fleet processes | `python scripts/stream_fleet.py stop` |

## Control API

The control API is local-first. Mutating endpoints require either a bearer token or an explicit local-lab override.

```bash
export SS_CONTROL_API_TOKEN=change-me
python scripts/stream_control_api.py --host 127.0.0.1 --port 18700
```

Temporary local override:

```bash
SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true
```

## Web Console

```bash
cd apps/stream-console
npm ci
npm run dev
```

The web console includes:

- fleet-only monitor telemetry
- preset session output
- graph editor with YAML import/export
- validate/run actions for graph specs

## Development Checks

Python:

```bash
python -m pytest
python scripts/release_readiness.py --profile lab-rc --json
```

Web console:

```bash
cd apps/stream-console
npm ci
npm run typecheck
npm run test
npm run build
```

CI workflow:

```text
.github/workflows/ci.yml
```

CI currently covers:

- Python tests on Ubuntu, Windows, and macOS
- no-Docker smoke checks
- docs, test hygiene, environment, plugin, policy, command-surface, and SSOT gates
- React/Vite console typecheck, tests, and build
- conda smoke checks on Ubuntu and Windows
- final `required-gate`

## Release Baseline

- Lab RC target: `v0.1.0-rc.1`
- Release checklist: `docs/guides/lab_rc_release_checklist.md`
- Execution SSOT: `docs/roadmap/execution_roadmap.md`

Required release gates:

```bash
python scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json
python scripts/command_surface_snapshot.py --check --baseline configs/policy/command_surface_snapshot_v1.json
python scripts/ssot_sync_check.py --strict --json
python scripts/release_readiness.py --profile lab-rc --json
```

## Documentation Map

- Docs index: `docs/index.md`
- Command reference: `docs/ops/command_reference.md`
- Node graph guide: `docs/guides/node_graph_guide.md`
- Graph wizard guide: `docs/guides/graph_wizard_guide.md`
- Demo pack guide: `docs/guides/demo_pack_guide.md`
- Local console guide: `docs/guides/local_console_quickstart.md`
- Block editor guide: `docs/guides/block_editor_quickstart.md`
- StreamPacket contract: `docs/contracts/stream_packet.md`
- Observability contract: `docs/contracts/observability.md`
- Doc-code mapping: `docs/reference/doc_code_mapping.md`

## License

Apache License 2.0 (`LICENSE`)
