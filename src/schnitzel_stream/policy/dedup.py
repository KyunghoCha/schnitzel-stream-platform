from __future__ import annotations

"""
Event dedup policy (ported from legacy).

Intent:
- Phase 4 legacy removal: port `ai.rules.dedup` into the platform namespace.
- Keep behavior compatible with the legacy implementation to make parity/cutover measurable.
"""

from dataclasses import dataclass, field
import time
from typing import Any


def build_dedup_key(payload: dict[str, Any]) -> str | None:
    camera_id = payload.get("camera_id")
    event_type = payload.get("event_type")
    if not camera_id or not event_type:
        return None

    track_id = payload.get("track_id")
    if track_id is not None:
        return f"{camera_id}:{event_type}:{track_id}"
    return f"{camera_id}:{event_type}:na"


@dataclass
class CooldownStore:
    cooldown_sec: float = 10.0
    prune_interval: int = 100
    _last_ts: dict[str, float] = field(default_factory=dict)
    _last_severity: dict[str, str] = field(default_factory=dict)
    _count: int = 0

    def _now(self) -> float:
        return time.monotonic()

    def allow(self, key: str, severity: str | None = None) -> bool:
        # Allow immediately if severity changed.
        if severity is not None:
            prev = self._last_severity.get(key)
            if prev is not None and prev != severity:
                self._last_severity[key] = severity
                self._last_ts[key] = self._now()
                return True

        now = self._now()
        last = self._last_ts.get(key)
        if last is None:
            self._last_ts[key] = now
            if severity is not None:
                self._last_severity[key] = severity
            return True

        if now - last < self.cooldown_sec:
            return False

        self._last_ts[key] = now
        if severity is not None:
            self._last_severity[key] = severity
        return True

    def prune(self) -> None:
        if self.cooldown_sec <= 0:
            return
        now = self._now()
        expired = [k for k, ts in self._last_ts.items() if (now - ts) > self.cooldown_sec]
        for k in expired:
            self._last_ts.pop(k, None)
            self._last_severity.pop(k, None)

    def tick(self) -> None:
        self._count += 1
        if self._count % max(1, self.prune_interval) == 0:
            self.prune()


@dataclass
class DedupController:
    cooldown_sec: float = 10.0
    prune_interval: int = 100
    store: CooldownStore | None = None

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = CooldownStore(self.cooldown_sec, self.prune_interval)

    def allow_emit(self, payload: dict[str, Any]) -> bool:
        key = build_dedup_key(payload)
        if key is None:
            return True  # No key -> skip dedup.

        severity = payload.get("severity")
        allowed = self.store.allow(key, severity)
        self.store.tick()
        return allowed

