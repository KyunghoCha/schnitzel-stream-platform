from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class StreamPacket:
    """Universal data contract for all nodes.

    SSOT: `docs/contracts/stream_packet.md`

    v1 (Phase B) is intentionally minimal:
    - `kind` identifies payload semantics (frame/event/sensor/metrics/...).
    - `source_id` identifies the origin stream (camera_id, sensor_id, etc).
    - `payload` carries data (often dict); nodes must not rely on out-of-band coupling.
    """

    packet_id: str
    ts: str
    kind: str
    source_id: str
    payload: Any
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        kind: str,
        source_id: str,
        payload: Any,
        ts: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> StreamPacket:
        return cls(
            packet_id=str(uuid4()),
            ts=ts or _now_iso_utc(),
            kind=str(kind),
            source_id=str(source_id),
            payload=payload,
            meta=dict(meta or {}),
        )
