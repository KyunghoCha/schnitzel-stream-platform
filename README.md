# schnitzel-stream-platform

Universal stream processing platform (edge-first).

- Stable entrypoint (SSOT): `python -m schnitzel_stream`
- Graph specs:
  - v1: job graph (legacy runtime indirection)
  - v2: node graph (in-proc DAG runtime)
- Contracts:
  - `StreamPacket`: `docs/contracts/stream_packet.md`
  - Observability (run report): `docs/contracts/observability.md`
- Execution plan SSOT: `docs/roadmap/execution_roadmap.md`

## Quickstart

Prereqs:

- Python 3.11

Install:

```bash
pip install -r requirements.txt
```

Environment:

```powershell
# Windows (recommended)
./setup_env.ps1

# Linux/macOS
export PYTHONPATH=src
```

Validate default graph (v1):

```bash
python -m schnitzel_stream validate
```

Run v2 in-proc demo graph:

```bash
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml

# JSON run report (metrics)
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --report-json
```

Durable queue demo (SQLite WAL):

```bash
python -m schnitzel_stream --graph configs/graphs/dev_durable_enqueue_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_durable_drain_ack_v2.yaml
```

## Plugin Policy (Safety)

By default, plugin loading is allowlisted to repo namespaces (`schnitzel_stream.*`, `ai.*`).

- `ALLOWED_PLUGIN_PREFIXES` (comma-separated prefixes)
- `ALLOW_ALL_PLUGINS=true` (dev only)

## Legacy Video Pipeline (Compatibility)

The legacy CCTV/video runtime is preserved under `src/ai/` and is executed via the v1 job graph (default).

- Behavior/spec: `docs/specs/pipeline_spec.md`
- Commands/runbook: `docs/ops/command_reference.md`

Intent: the repo direction is a universal stream platform; the legacy pipeline is maintained as a compatibility/reference runtime during the migration.

## Docs

Start here:

- `docs/index.md`

Key SSOT docs:

- `docs/roadmap/execution_roadmap.md`
- `docs/roadmap/strategic_roadmap.md`
- `docs/contracts/stream_packet.md`
- `docs/contracts/observability.md`

## License

Apache 2.0. See `LICENSE`.
