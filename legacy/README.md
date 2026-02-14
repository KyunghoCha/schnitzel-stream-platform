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

- v1 legacy runtime deprecated: **2026-02-14**
- Earliest removal date: **2026-05-15**

SSOT: `docs/roadmap/execution_roadmap.md`, `docs/roadmap/legacy_decommission.md`

## Policy (Freeze)

- Allowed: security fixes, crash fixes, data-loss fixes.
- Not allowed: new features, new configuration keys, new plugin boundaries.

