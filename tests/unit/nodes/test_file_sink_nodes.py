from __future__ import annotations

import json
from pathlib import Path

import pytest

from schnitzel_stream.nodes.file_sink import JsonFileSink, JsonlSink
from schnitzel_stream.packet import StreamPacket


def test_jsonl_sink_requires_path():
    with pytest.raises(ValueError):
        JsonlSink(config={})


def test_jsonl_sink_writes_packet_line(tmp_path: Path):
    out = tmp_path / "events.jsonl"
    sink = JsonlSink(config={"path": str(out), "body": "packet", "flush": True})

    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e1"}, meta={"k": "v"})
    try:
        assert list(sink.process(pkt)) == []
    finally:
        sink.close()

    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["packet_id"] == pkt.packet_id
    assert rec["source_id"] == "cam01"
    assert rec["payload"]["event_id"] == "e1"


def test_jsonl_sink_payload_mode_writes_payload_only(tmp_path: Path):
    out = tmp_path / "payloads.jsonl"
    sink = JsonlSink(config={"path": str(out), "body": "payload"})

    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e2"})
    try:
        sink.process(pkt)
    finally:
        sink.close()

    rec = json.loads(out.read_text(encoding="utf-8").strip())
    assert rec == {"event_id": "e2"}


def test_jsonl_sink_raises_on_non_serializable_payload(tmp_path: Path):
    out = tmp_path / "bad.jsonl"
    sink = JsonlSink(config={"path": str(out)})
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"bad": object()})

    try:
        with pytest.raises(TypeError):
            list(sink.process(pkt))
    finally:
        sink.close()


def test_json_file_sink_writes_one_file_per_packet(tmp_path: Path):
    out_dir = tmp_path / "packets"
    sink = JsonFileSink(config={"dir": str(out_dir), "body": "payload", "filename_template": "{seq:03d}_{kind}.json"})

    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e3"})
    assert list(sink.process(pkt)) == []

    files = sorted(out_dir.glob("*.json"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text(encoding="utf-8"))
    assert rec == {"event_id": "e3"}


def test_json_file_sink_sanitizes_filename_and_can_forward(tmp_path: Path):
    out_dir = tmp_path / "packets"
    sink = JsonFileSink(
        config={
            "dir": str(out_dir),
            "filename_template": "../escape.json",
            "body": "packet",
            "forward": True,
            "meta_key": "artifact",
        }
    )

    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e4"})
    out = list(sink.process(pkt))

    files = sorted(out_dir.glob("*.json"))
    assert len(files) == 1
    assert files[0].name == "escape.json"
    assert files[0].parent == out_dir

    assert len(out) == 1
    assert out[0].meta["artifact"]["path"].endswith("escape.json")


def test_json_file_sink_raises_on_non_serializable_payload(tmp_path: Path):
    out_dir = tmp_path / "packets"
    sink = JsonFileSink(config={"dir": str(out_dir)})
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"bad": object()})

    with pytest.raises(TypeError):
        list(sink.process(pkt))
