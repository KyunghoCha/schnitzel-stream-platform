from __future__ import annotations

import json
import time

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.packs.experiments.nodes.backpressure import (
    BackpressureMetricsSink,
    generate_event_plan,
)


def test_generate_event_plan_is_deterministic_and_burst_aware():
    cfg = {
        "total_events": 4,
        "groups": ["g1", "g2"],
        "group_probs": {"g1": 1.0, "g2": 0.0},
        "burst_every": 2,
        "burst_size": 3,
        "event_interval_ms": 5.0,
        "recovery_marker_seq": 4,
    }
    a = generate_event_plan(cfg, seed=7)
    b = generate_event_plan(cfg, seed=7)
    assert a == b
    assert len(a) == 8
    assert a[4].recovery_marker is True
    assert all(item.group_id == "g1" for item in a)


def test_backpressure_metrics_sink_writes_latency_rows(tmp_path):
    output_path = tmp_path / "events.jsonl"
    sink = BackpressureMetricsSink(config={"output_path": str(output_path), "flush": True})
    emitted_ns = time.monotonic_ns()
    pkt = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"seq": 1, "group_id": "g1", "logical_ts_ms": 10.0},
        meta={"seq": 1, "group_id": "g1", "emitted_mono_ns": emitted_ns, "recovery_marker": True},
    )
    try:
        out = list(sink.process(pkt))
        assert out == []
        metrics = sink.metrics()
        assert metrics["written_total"] == 1
        assert metrics["recovery_marker_seen_total"] == 1
    finally:
        sink.close()

    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["seq"] == 1
    assert rows[0]["group_id"] == "g1"
    assert rows[0]["recovery_marker"] is True
    assert isinstance(rows[0]["latency_ms"], float)

