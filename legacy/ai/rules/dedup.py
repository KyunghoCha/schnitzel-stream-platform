# Docs: docs/implementation/30-event-dedup/README.md
from __future__ import annotations

# 이벤트 중복 억제(dedup) 모듈
# - keying 전략
# - cooldown store
# - severity override

from dataclasses import dataclass, field
import time
from typing import Any


def build_dedup_key(payload: dict[str, Any]) -> str | None:
    # payload에서 dedup key 생성
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
    # key별 마지막 emit 시각 저장
    cooldown_sec: float = 10.0
    prune_interval: int = 100
    _last_ts: dict[str, float] = field(default_factory=dict)
    _last_severity: dict[str, str] = field(default_factory=dict)
    _count: int = 0

    def _now(self) -> float:
        # monotonic time 사용
        return time.monotonic()

    def allow(self, key: str, severity: str | None = None) -> bool:
        # severity 변경 시 즉시 허용
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
        # 오래된 key 정리
        if self.cooldown_sec <= 0:
            return
        now = self._now()
        expired = [k for k, ts in self._last_ts.items() if (now - ts) > self.cooldown_sec]
        for k in expired:
            self._last_ts.pop(k, None)
            self._last_severity.pop(k, None)

    def tick(self) -> None:
        # 일정 횟수마다 prune
        self._count += 1
        if self._count % max(1, self.prune_interval) == 0:
            self.prune()


@dataclass
class DedupController:
    # dedup 전체 제어기
    cooldown_sec: float = 10.0
    prune_interval: int = 100
    store: CooldownStore | None = None

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = CooldownStore(self.cooldown_sec, self.prune_interval)

    def allow_emit(self, payload: dict[str, Any]) -> bool:
        # payload 기준으로 emit 허용 여부 판단
        key = build_dedup_key(payload)
        if key is None:
            return True  # key가 없으면 dedup 미적용

        severity = payload.get("severity")
        allowed = self.store.allow(key, severity)
        self.store.tick()
        return allowed
