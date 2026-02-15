# Docs: docs/packs/vision/event_protocol_v0.2.md
from __future__ import annotations

# 이벤트 스키마/더미 이벤트 생성기
# - protocol.md 필드 구조에 맞춤

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from zoneinfo import ZoneInfo as TzInfo
except Exception:  # pragma: no cover
    TzInfo = None  # type: ignore[assignment]


@dataclass
class BBox:
    # 바운딩 박스 좌표
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class ZoneResult:
    # zone inside 결과
    zone_id: str
    inside: bool


@dataclass
class DummyEvent:
    # 더미 이벤트 payload 구조
    event_id: str
    ts: str
    site_id: str
    camera_id: str
    event_type: str
    object_type: str
    severity: str
    track_id: int | None
    bbox: BBox
    confidence: float
    zone: ZoneResult
    snapshot_path: str | None

    def to_payload(self) -> dict[str, Any]:
        # dataclass -> dict 변환
        return asdict(self)


def _now_iso(tz_name: str | None) -> str:
    # timezone 설정이 있으면 해당 타임존 ISO-8601 생성
    if tz_name and TzInfo is not None:
        try:
            return datetime.now(TzInfo(tz_name)).isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def build_event_scaffold(
    site_id: str,
    camera_id: str,
    tz_name: str | None = None,
    ts_override: str | None = None,
) -> dict[str, Any]:
    """이벤트 공통 필드 scaffold 생성 (production-safe).

    event_id, ts, site_id, camera_id, zone 기본값, snapshot_path=None 을 포함한다.
    event_type, object_type 등 탐지 관련 필드는 호출자가 채워야 한다.
    """
    return {
        "event_id": str(uuid4()),
        "ts": ts_override or _now_iso(tz_name),
        "site_id": site_id,
        "camera_id": camera_id,
        "event_type": "",
        "object_type": "",
        "severity": "",
        "track_id": None,
        "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
        "confidence": 0.0,
        "zone": {"zone_id": "", "inside": False},
        "snapshot_path": None,
    }


def build_dummy_event(site_id: str, camera_id: str, frame_index: int, tz_name: str | None = None) -> DummyEvent:
    # 더미 이벤트 생성 (mock/test 전용)
    ts = _now_iso(tz_name)
    bbox = BBox(x1=10 + (frame_index % 100), y1=20, x2=200, y2=260)
    return DummyEvent(
        event_id=str(uuid4()),
        ts=ts,
        site_id=site_id,
        camera_id=camera_id,
        event_type="ZONE_INTRUSION",
        object_type="PERSON",
        severity="LOW",
        track_id=frame_index % 100,
        bbox=bbox,
        confidence=0.75,
        zone=ZoneResult(zone_id="Z0", inside=False),
        snapshot_path=None,
    )
