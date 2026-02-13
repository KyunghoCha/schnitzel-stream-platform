# Support Matrix (Edge-First, PROVISIONAL)

Last updated: 2026-02-13

## Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Define a pragmatic support matrix and packaging strategy for "runs on almost all edges" goals.
- **Non-scope**: GPU/accelerator-specific builds (Jetson/CUDA/DirectML) are not standardized in Phase 0.

## Risks (P0–P3)

- **P0**: A single packaging method will not cover all edge environments (Docker unavailable, restricted OS images, no compiler toolchain).
- **P1**: OpenCV and video decode dependencies vary by OS/arch; binary wheels may not exist for niche targets.
- **P2**: Windows service/daemonization semantics differ from Linux systemd; operational parity requires extra work.
- **P3**: Shipping "one binary" builds can mask dynamic dependency issues and complicate debugging.

## Mismatches (path)

- None found. (This document establishes the current support intent; implementation will be incremental.)

## Fix Plan

1. **Baseline runtime** (Phase 0):
   - Python **3.11** (CI baseline).
   - Entrypoint: `python -m schnitzel_stream`.
2. **Primary distribution (Linux edges)**:
   - Use Docker images (multi-arch): `linux/amd64`, `linux/arm64`.
   - Build via `docker buildx` in CI when ready.
3. **Developer distribution (Windows/macOS/Linux)**:
   - Run from source with `PYTHONPATH=src` and a venv.
   - Keep dependencies minimal; keep heavy runtimes as optional requirements files.
4. **Optional "single artifact" distribution (select targets)**:
   - Evaluate PyInstaller/Nuitka only after Phase 1 runtime boundaries are clearer.
   - Treat as convenience builds, not the primary ops path.
5. **Operational contracts**:
   - Repo-root relative configs: `configs/*`.
   - Writable paths must be explicit (snapshots/logs/outputs) and documented per target.

## Verification

- Executed: N/A (doc-only change).
- Not executed: N/A.

## Open Questions

- What is the official target list?
  - OS: Linux, Windows, macOS
  - Arch: amd64, arm64
  - Edge class: Raspberry Pi / industrial PC / Jetson
- Do we require Docker on all production edges, or do we need a "no-Docker" packaging lane?
- How should we handle GPU acceleration portability (CUDA vs OpenVINO vs DirectML)?

