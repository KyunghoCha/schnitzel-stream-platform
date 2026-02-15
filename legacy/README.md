# Legacy Runtime (Quarantined)

This folder contains the legacy AI/CCTV runtime (import path: `ai.*`).

Intent:
- Keep legacy code available during the deprecation window.
- Prevent new development from accreting onto the legacy surface.

## Location / Import Path

- Source code: `legacy/ai/**`
- Compatibility shim: `src/ai/__init__.py`
  - Keeps `import ai...` working by adding `legacy/` to `sys.path`.

## How To Run (Legacy v1 Graph)

```bash
python -m schnitzel_stream --graph configs/graphs/legacy_pipeline.yaml
```

## Deprecation

- v1 legacy runtime is deprecated (see Phase 4 `P4.3`).
- Removal is gated by the deprecation window (>= 90 days after `P4.3`).

SSOT: `docs/roadmap/execution_roadmap.md`, `docs/roadmap/legacy_decommission.md`

## Policy (Freeze)

- Allowed: security fixes, crash fixes, data-loss fixes.
- Not allowed: new features, new configuration keys, new plugin boundaries.
