# Docs: docs/specs/model_interface.md, docs/contracts/protocol.md
from __future__ import annotations

# 이벤트 빌더 추상화/더미 구현

from dataclasses import dataclass
import logging
from typing import Protocol, Any

from ai.events.schema import build_dummy_event, build_event_scaffold
from ai.events.snapshot import build_snapshot_path, save_snapshot, to_public_path
from ai.pipeline.model_adapter import ModelAdapter

logger = logging.getLogger(__name__)


class EventBuilder(Protocol):
    # 이벤트 생성 인터페이스
    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        ...


def _maybe_save_snapshot(
    payload: dict[str, Any],
    frame: Any,
    snapshot_base_dir: str | None,
    snapshot_public_prefix: str | None,
) -> None:
    if not snapshot_base_dir:
        return
    ts = payload.get("ts")
    track_id = payload.get("track_id")
    fpath = build_snapshot_path(snapshot_base_dir, payload["site_id"], payload["camera_id"], ts, track_id)
    saved = save_snapshot(frame, fpath)
    if saved is not None:
        payload["snapshot_path"] = to_public_path(saved, snapshot_base_dir, snapshot_public_prefix)


def _is_valid_detection(det: dict[str, Any]) -> bool:
    required = ("bbox", "confidence", "event_type", "object_type", "severity")
    if any(k not in det for k in required):
        return False
    bbox = det.get("bbox")
    if not isinstance(bbox, dict):
        return False
    for key in ("x1", "y1", "x2", "y2"):
        if key not in bbox:
            return False
    if det.get("object_type") == "PERSON" and det.get("track_id") is None:
        return False
    return True


@dataclass
class DummyEventBuilder:
    # 더미 이벤트 생성기 (향후 실제 모델 출력으로 교체)
    site_id: str
    camera_id: str
    timezone: str | None = None
    snapshot_base_dir: str | None = None
    snapshot_public_prefix: str | None = None

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        # frame은 현재 사용하지 않지만, 추후 모델 입력을 위해 유지
        payload = build_dummy_event(self.site_id, self.camera_id, frame_idx, self.timezone).to_payload()

        # 스냅샷 저장 (옵션)
        _maybe_save_snapshot(payload, frame, self.snapshot_base_dir, self.snapshot_public_prefix)

        return [payload]


@dataclass
class MockModelEventBuilder:
    # 모델/트래커를 대체하는 mock 이벤트 빌더
    site_id: str
    camera_id: str
    timezone: str | None = None
    snapshot_base_dir: str | None = None
    snapshot_public_prefix: str | None = None

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        payload = build_dummy_event(self.site_id, self.camera_id, frame_idx, self.timezone).to_payload()
        payload["event_type"] = "ZONE_INTRUSION"
        payload["object_type"] = "PERSON"
        payload["severity"] = "LOW"
        payload["confidence"] = 0.75

        _maybe_save_snapshot(payload, frame, self.snapshot_base_dir, self.snapshot_public_prefix)

        return [payload]


@dataclass
class RealModelEventBuilder:
    # 실제 모델/트래커 출력 기반 이벤트 빌더 (어댑터 필요)
    site_id: str
    camera_id: str
    adapter: ModelAdapter
    timezone: str | None = None
    snapshot_base_dir: str | None = None
    snapshot_public_prefix: str | None = None

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        detections = self.adapter.infer(frame)
        if detections is None:
            return []
        if isinstance(detections, dict):
            detections = [detections]
        # 프레임 내 모든 객체 감지에 대해 동일한 프레임 타임스탬프 유지.
        frame_scaffold = build_event_scaffold(self.site_id, self.camera_id, self.timezone)
        frame_ts = frame_scaffold["ts"]
        payloads: list[dict[str, Any]] = []
        for det in detections:
            if not isinstance(det, dict) or not _is_valid_detection(det):
                logger.warning("invalid model detection, skipping", extra={"error_code": "MODEL_DET_INVALID"})
                continue
            payload = build_event_scaffold(self.site_id, self.camera_id, self.timezone, ts_override=frame_ts)
            payload["event_type"] = det["event_type"]
            payload["object_type"] = det["object_type"]
            payload["severity"] = det["severity"]
            payload["confidence"] = float(det["confidence"])
            payload["bbox"] = det["bbox"]
            payload["track_id"] = det.get("track_id")
            _maybe_save_snapshot(payload, frame, self.snapshot_base_dir, self.snapshot_public_prefix)
            payloads.append(payload)
        return payloads
