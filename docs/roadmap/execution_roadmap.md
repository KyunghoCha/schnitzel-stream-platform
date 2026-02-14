# Execution Roadmap (Platform Pivot SSOT)

Last updated: 2026-02-14

This document is the **execution SSOT** for the platform pivot.

Current step id: `P4.2.3`

Rule:
- When reporting progress (in issues/PRs/chat), always reference the **current step id** (example: `P1.4/8`).

## Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/contracts/stream_packet.md`, `PROMPT_CORE.md`.
- **Scope**: Track the ordered plan, status, and next actions for evolving `schnitzel-stream-platform` into a universal stream platform with a stable entrypoint.
- **Non-scope**: Final DAG semantics, distributed execution, and autopilot control plane (these are phased and provisional).

## Risks (P0–P3)

- **P0**: Plan drift: adding features without updating step status causes SSOT/code mismatch.
- **P1**: Over-design: locking DAG/type systems too early can block shipping.
- **P2**: Under-design: shipping runtime without validation/backpressure risks instability on edge.
- **P3**: Doc fragmentation: multiple “plans” competing as SSOT.

## Mismatches (path)

- Legacy CCTV-only roadmap is preserved at `docs/roadmap/legacy_cctv_execution_roadmap_2026-02-08.md` (historical reference, not SSOT).

## Fix Plan

Status legend:
- `DONE`: completed and merged on `main`
- `NOW`: next work to execute
- `NEXT`: queued after NOW
- `LATER`: not started

### Phase 0: Entrypoint SSOT + Strangler (DONE ~100%)

- `P0.1` Cross-platform LF canonical (`.gitattributes`). `DONE` (291874c)
- `P0.2` Introduce `schnitzel_stream` core skeleton. `DONE` (287abde)
- `P0.3` Phase 0 job spec + legacy job runner. `DONE` (29cb3ed)
- `P0.4` New CLI entrypoint `python -m schnitzel_stream`. `DONE` (5cd6c43)
- `P0.5` Migrate tests/scripts/Docker/docs, disable legacy CLI. `DONE` (c729fb9, 62786b7, aa8d515)
- `P0.6` SSOT docs for pivot (architecture/plan/support matrix/roadmap refinement). `DONE` (5e30823, 151676c, 4f1ab87, 92567af)
- `P0.7` StreamPacket contract SSOT + references. `DONE` (f34f876)

Current position: **Phase 4** (legacy decommission is now the priority; `P3.3` is deferred)

### Phase 1: Graph Runtime MVP (strict DAG) + StreamPacket Adoption (DONE ~100%)

- `P1.1` Draft graph model + strict DAG validator + unit tests. `DONE` (27bb702)
- `P1.2` Draft node-graph spec v2 loader + unit tests. `DONE` (2822ffa, 87d7a24)
- `P1.3` Centralize plugin allowlist checks in `PluginPolicy`. `DONE` (4d95fd5)
- `P1.4` CLI: add `validate` / `--validate-only` to validate v1(job) and v2(node graph). `DONE` (f4322d4)
- `P1.5` Runtime MVP: execute v2 graph (topological order) for in-proc packets only. `DONE` (7e1a9e7)
- `P1.6` Type/port/transport-compat validation (static). `DONE` (3fe090a)
- `P1.7` Restricted cycles policy (Delay/InitialValue only) as a validator extension. `DONE` (53b38a9)

### Phase 2: Durable Delivery Hardening (DONE ~100%)

- `P2.1` Durable queue node plugin (`WAL/SQLite`), store-and-forward. `DONE` (fd02823)
- `P2.2` Idempotency keys and ack semantics. `DONE` (e885e41)
- `P2.3` Soak tests for outage/restart/backlog replay. `DONE` (9dabf8d)

### Phase 3: Control Plane (IN PROGRESS ~60–75%)

- `P3.1` Unified metrics/health contract across transports. `DONE` (e6d14c5)
- `P3.2` Autonomic tuning hooks (policy-driven throttles). `DONE` (a792677)
- `P3.3` Optional LLM/controller layer (human-in-the-loop, gated). `NEXT` (optional)

### Phase 4: Legacy Decommission (IN PROGRESS)

Intent:
- Remove `src/ai/*` only after v2 graphs cover the required production behavior.
- Prefer extraction (separate package/repo) over hard-delete if external users still depend on it.
- Legacy removal requires a **deprecation window**: do not delete `src/ai/*` earlier than **90 days after** `P4.3` lands.

- `P4.1` Define v2 parity scope + cutover criteria (what “legacy can be removed” means). `DONE` (ba2cb85) (SSOT: `docs/roadmap/legacy_decommission.md`)
- `P4.2` Implement v2 CCTV pipeline graph + nodes to reach parity (source/model/policy/sink). `IN PROGRESS`
  - `P4.2.1` Port critical policy nodes (zones/dedup) into `schnitzel_stream` + tests + demo graph. `DONE` (ba6ea9d, 2ef7481, 1b0aa83, d14abcf)
  - `P4.2.2` v2 event builder (protocol v0.2) node + tests. `DONE` (8860377, 618b20a, 8f558b2)
  - `P4.2.3` v2 file-video source + sampler nodes + tests. `NOW`
- `P4.3` Switch default graph to v2 and start a deprecation window for v1 legacy job. `NEXT`
- `P4.4` Extract legacy runtime (`src/ai/*`) to a separate package/repo or move under `legacy/` with pinned deps. `LATER`
- `P4.5` Remove legacy runtime from main tree after the deprecation window. `LATER`

## Verification

- Executed (local): `python3 -m compileall -q src tests`
- Not executed (local): `pytest` (depends on venv deps; CI should enforce on push)

## Open Questions

- What is the Phase 1 runtime execution model?
  - push vs pull, batching/windowing, and backpressure semantics
- What is the minimal port/type system to prevent invalid graphs without overfitting to CCTV?
- What is the official edge support matrix (OS/arch/GPU) and packaging lane policy (Docker required or optional)?
