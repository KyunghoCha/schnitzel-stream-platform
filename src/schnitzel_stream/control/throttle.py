from __future__ import annotations

"""
Policy-driven throttle hooks (Phase 3 draft).

Intent:
- Provide a minimal control-plane hook to cap work on constrained edge devices.
- Keep policies deterministic and testable (avoid time-based rate limits in the core).
"""

from dataclasses import dataclass
from typing import Protocol


class ThrottlePolicy(Protocol):
    def allow_source_emit(self, *, node_id: str, emitted_total: int) -> bool:
        """Return False to stop emitting more packets from this run."""


@dataclass(frozen=True)
class NoopThrottle:
    def allow_source_emit(self, *, node_id: str, emitted_total: int) -> bool:
        return True


@dataclass(frozen=True)
class FixedBudgetThrottle:
    """Stop the run after emitting N packets from all source nodes."""

    max_source_emits_total: int

    def allow_source_emit(self, *, node_id: str, emitted_total: int) -> bool:
        return int(emitted_total) < int(self.max_source_emits_total)

