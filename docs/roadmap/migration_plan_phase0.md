# Phase 0 Migration Plan (Universal Platform SSOT)

Last updated: 2026-02-14

Note:
- Phase 0 is complete. This document is kept as historical context.
- Current default graph is v2: `configs/graphs/dev_cctv_e2e_mock_v2.yaml` (see `docs/roadmap/execution_roadmap.md`).

## Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Phase 0 "Strangler" migration to make `python -m schnitzel_stream` the single supported runtime entrypoint, while executing the existing `ai.pipeline` runtime as a legacy job.
- **Non-scope**: Full DAG runtime, distributed execution, and finalized long-term StreamPacket schema (these remain provisional).

## Risks (P0–P3)

- **P0**: Existing users/automation still calling `python -m ai.pipeline` will hard-fail.
- **P1**: Phase 0 graph spec is job-only; config validation is intentionally limited and may allow invalid future graphs.
- **P2**: Plugin allowlist may block experimental adapters in dev environments.
- **P3**: Cross-platform line ending drift (CRLF/LF) can create noisy diffs and operational surprises.

## Mismatches (path)

- None found.

## Fix Plan

1. **Cross-platform hygiene**: enforce canonical LF line endings with `.gitattributes` to prevent CRLF noise in diffs and containers.
2. **New platform package**: introduce `src/schnitzel_stream/` as the universal platform namespace (StreamPacket/Node/PluginPolicy).
3. **Phase 0 graph spec**: add minimal `GraphSpec` loader (YAML) with explicit versioning.
4. **Phase 0 legacy job**: implement `LegacyAIPipelineJob` that runs `ai.pipeline` runtime via the new platform entrypoint.
5. **New CLI**: implement `python -m schnitzel_stream` as the stable entrypoint.
   - Phase 0 default graph was `configs/graphs/legacy_pipeline.yaml` (v1 job graph).
   - Phase 4 default graph is `configs/graphs/dev_cctv_e2e_mock_v2.yaml` (v2 node graph).
6. **Test migration**: switch subprocess integration/regression tests from `-m ai.pipeline` to `-m schnitzel_stream`.
7. **Disable legacy CLI**: keep `legacy/ai/pipeline/__main__.py` but make it fail-fast with a clear migration message.
8. **Ops + docs migration**: update Docker CMD, scripts, and docs to reference `python -m schnitzel_stream` instead of `python -m ai.pipeline`.
9. **SSOT documents (this change-set)**: add `docs/design/architecture_2.0.md`, update `docs/index.md` and `docs/specs/pipeline_spec.md` to reflect the new entrypoint and Phase 0 indirection.

## Verification

- Executed:
  - `python3 -m compileall -q src/schnitzel_stream`
  - `python3 -m compileall -q src scripts tests`
- Not executed:
  - `pytest` (local runtime/tooling not available in this environment; CI should validate on push).

## Open Questions

- GraphSpec evolution: job-only (Phase 0) -> DAG runtime (Phase 1+). What is the versioning and backward-compat policy?
- Cross-platform packaging: Docker-only vs pip/venv vs PyInstaller. What is the official support matrix (OS/arch/GPU)?
- StreamPacket contract: typed payload vs `Any`, serialization boundaries, and handling of large/binary frame payloads.
- Security posture for plugins: what is the prod policy for plugin loading and distribution?
