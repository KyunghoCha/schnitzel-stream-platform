from __future__ import annotations

"""
Legacy compatibility package: `ai.*`

Intent:
- Phase 4 quarantines legacy code under `legacy/ai/**` while keeping import paths stable.
- New code must live under `schnitzel_stream.*` (platform-owned).

Deprecation:
- v1 legacy runtime is deprecated as part of Phase 4 (`P4.3`).
- Removal is gated by the deprecation window (>= 90 days after `P4.3`).
"""

from pathlib import Path
from pkgutil import extend_path
import sys
import warnings


warnings.warn(
    "`ai.*` is legacy and quarantined under `legacy/ai/**`. "
    "Use `schnitzel_stream.*` for new development. "
    "Legacy removal is tracked in `docs/roadmap/execution_roadmap.md`.",
    DeprecationWarning,
    stacklevel=2,
)


_legacy_root = Path(__file__).resolve().parents[2] / "legacy"
if _legacy_root.exists():
    p = str(_legacy_root)
    if p not in sys.path:
        # Intent: make `legacy/ai/**` importable without changing PYTHONPATH.
        sys.path.insert(0, p)

# Intent: allow resolving submodules from both `src/ai` (shim) and `legacy/ai`.
__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]
