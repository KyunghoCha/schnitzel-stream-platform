# Architecture 2.0 (PROVISIONAL)

Last updated: 2026-02-13

Intent:
- This document is **provisional**. The platform pivot is in progress and the roadmap may change.
- Phase 0 intentionally runs the legacy `ai.pipeline` runtime through the new `schnitzel_stream` entrypoint (Strangler pattern).

## Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/roadmap/migration_plan_phase0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Define the platform boundaries and the Phase 0/1 execution model for the universal stream platform namespace `schnitzel_stream`.
- **Non-scope**: Finalized DAG semantics, distributed scheduling, and any promise of stable public API beyond the CLI entrypoint in Phase 0.

## Boundary Map

- **Platform core (new)**: `src/schnitzel_stream/`
  - CLI entrypoint: `python -m schnitzel_stream` (`src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py`)
  - Minimal graph spec: `src/schnitzel_stream/graph/spec.py` (Phase 0 job indirection)
  - Plugin loading policy: `src/schnitzel_stream/plugins/registry.py` (allowlist by default)
  - Core abstractions (early): `src/schnitzel_stream/packet.py`, `src/schnitzel_stream/node.py`
- **Legacy runtime (kept for Phase 0)**: `src/ai/`
  - The "AI pipeline" remains implemented under `ai.*` modules.
  - Execution is routed via `schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob`.

## Critical Dependencies

- Python: **3.11** baseline (CI matrix).
- `omegaconf`: config + graph spec parsing.
- OpenCV: optional at runtime (visualization / frame decode paths); keep GUI as an opt-in flag.
- OS facilities: filesystem paths, networking, and signals (best-effort on Windows).

## Evolution Constraints

- CLI stability: `python -m schnitzel_stream` must remain the stable entrypoint as the platform evolves.
- Determinism: default config paths must not depend on CWD (tests/Docker/edge must behave the same).
- Side effects: keep I/O in adapters/jobs; core abstractions must remain reusable without RTSP/backend assumptions.
- Plugin safety: default should be production-safe (allowlist); dev can override via env explicitly.

## Risks (P0–P3)

- **P0**: Running arbitrary code via plugin loading is a security risk if policy is too permissive.
- **P1**: Phase 0 job-only graph spec can become accidental long-term API; must version early.
- **P2**: Cross-platform behavior drift (paths, signals, OpenCV, RTSP transports) can fragment edge support.
- **P3**: Doc/code drift during pivot (legacy docs still present); requires explicit SSOT mapping and updates.

## Mismatches (path)

- None found.

## Fix Plan

1. Phase 0 (now): stabilize the new entrypoint and keep legacy job execution reliable.
2. Phase 1: introduce a real DAG runtime that executes `Node` graphs with `StreamPacket` as the only contract.
3. Phase 1+: migrate legacy capabilities into plugins/nodes incrementally (sources, sensors, emitters, zones).
4. Phase 2+: add static graph validation (ports/types/transport compatibility) and policy-driven runtime tuning.

## Verification

- Executed: `python3 -m compileall -q src/schnitzel_stream`.
- Not executed: end-to-end runtime validation on real RTSP devices (hardware not available here).

## Open Questions

- Packaging strategy for "almost all edges": what is the official support matrix (Windows/macOS/Linux, amd64/arm64, Jetson/GPU)?
- How do we represent large payloads (frames) in StreamPacket without forcing serialization/copies?
- Where should long-lived state live (State Node vs external store vs blackboard), and what is the failure model?
