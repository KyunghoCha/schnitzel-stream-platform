from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any

from ai.events.schema import build_dummy_event
from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.events import EventBuilder
from ai.pipeline.sources import FrameSource
from ai.pipeline.emitter import EventEmitter
from ai.utils.metrics import MetricsTracker, Heartbeat
from ai.rules.zones import ZoneEvaluator
from ai.pipeline.events import RealModelEventBuilder
from ai.pipeline.model_adapter import ModelAdapter
from ai.utils.metrics import build_metrics_log


@dataclass
class _OneFrameSource:
    camera_id: str = "cam01"
    supports_reconnect: bool = False
    _read_count: int = 0

    @property
    def is_live(self) -> bool:
        return False

    def read(self) -> tuple[bool, Any]:
        if self._read_count == 0:
            self._read_count += 1
            return True, object()
        return False, None

    def release(self) -> None:
        return None

    def fps(self) -> float:
        return 30.0


class _NeverSample:
    def should_sample(self, frame_idx: int) -> bool:
        return False


@dataclass
class _NoopEmitter:
    def emit(self, payload: dict[str, Any]) -> bool:
        return True

    def close(self) -> None:
        pass


@dataclass
class _DummyBuilder(EventBuilder):
    site_id: str = "S001"
    camera_id: str = "cam01"

    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [build_dummy_event(self.site_id, self.camera_id, frame_idx, None).to_payload()]


def test_pipeline_counts_drops_when_sampler_skips() -> None:
    metrics = MetricsTracker(interval_sec=9999)
    ctx = PipelineContext(
        source=_OneFrameSource(),
        sampler=_NeverSample(),
        event_builder=_DummyBuilder(),
        emitter=_NoopEmitter(),
        metrics=metrics,
    )
    Pipeline(ctx).run(max_events=1)
    assert metrics.frames == 1
    assert metrics.drops == 1


def test_metrics_tracker_separates_emit_accept_and_backend_ack() -> None:
    metrics = MetricsTracker(interval_sec=9999)
    metrics.on_event()
    metrics.on_event()
    metrics.on_backend_ack(True)
    metrics.on_backend_ack(False)
    metrics.on_sensor_packet()
    metrics.on_sensor_drop()
    metrics.on_sensor_error()
    metrics.on_fusion_attempt(True)
    metrics.on_fusion_attempt(False)

    snap = metrics.snapshot()
    assert snap["events"] == 2
    assert snap["events_accepted"] == 2
    assert snap["backend_ack_ok"] == 1
    assert snap["backend_ack_fail"] == 1
    assert snap["sensor_packets_total"] == 1
    assert snap["sensor_packets_dropped"] == 1
    assert snap["sensor_source_errors"] == 1
    assert snap["fusion_attempts"] == 2
    assert snap["fusion_hits"] == 1
    assert snap["fusion_misses"] == 1

    payload = build_metrics_log(snap)
    assert payload["events"] == 2
    assert payload["events_accepted"] == 2
    assert payload["backend_ack_ok"] == 1
    assert payload["backend_ack_fail"] == 1
    assert payload["sensor_packets_total"] == 1
    assert payload["sensor_packets_dropped"] == 1
    assert payload["sensor_source_errors"] == 1
    assert payload["fusion_attempts"] == 2
    assert payload["fusion_hits"] == 1
    assert payload["fusion_misses"] == 1


def test_heartbeat_snapshot_includes_camera_id() -> None:
    hb = Heartbeat(interval_sec=9999)
    out = hb.snapshot(last_frame_ts=None, camera_id="cam99", sensor_last_packet_age_sec=0.42)
    assert out["camera_id"] == "cam99"
    assert out["sensor_last_packet_age_sec"] == 0.42


def test_zone_evaluator_empty_zones_sets_default() -> None:
    evaluator = ZoneEvaluator(
        source="file",
        site_id="S001",
        camera_id="cam01",
        rule_map={},
        file_path=None,
        cache_ttl_sec=0,
    )
    payload = build_dummy_event("S001", "cam01", 0, None).to_payload()
    payload = evaluator.apply(payload)
    assert payload["zone"]["zone_id"] == ""
    assert payload["zone"]["inside"] is False


@dataclass
class _AdapterMissingTrack(ModelAdapter):
    def infer(self, frame: Any) -> list[dict[str, Any]]:
        return [
            {
                "event_type": "ZONE_INTRUSION",
                "object_type": "PERSON",
                "severity": "LOW",
                "confidence": 0.9,
                "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
                # track_id missing on purpose
            }
        ]


def test_person_track_id_required_is_enforced() -> None:
    builder = RealModelEventBuilder(
        site_id="S001",
        camera_id="cam01",
        adapter=_AdapterMissingTrack(),
    )
    out = builder.build(0, object())
    assert out == []


def test_metrics_tracker_thread_safe_counters() -> None:
    metrics = MetricsTracker(interval_sec=9999)
    loops = 3000
    workers = 8

    def _work() -> None:
        for _ in range(loops):
            metrics.on_event()
            metrics.on_backend_ack(True)
            metrics.on_fusion_attempt(True)

    threads = [threading.Thread(target=_work) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    snap = metrics.snapshot()
    expected = loops * workers
    assert snap["events"] == expected
    assert snap["events_accepted"] == expected
    assert snap["backend_ack_ok"] == expected
    assert snap["fusion_attempts"] == expected
    assert snap["fusion_hits"] == expected
