from __future__ import annotations

from io import BytesIO
import json
from urllib import error

import pytest

import schnitzel_stream.nodes.http as http_mod
from schnitzel_stream.nodes.http import HttpJsonSink
from schnitzel_stream.packet import StreamPacket


class _FakeResponse:
    def __init__(self, status: int, body: bytes = b"{}"):
        self._status = int(status)
        self._body = body

    def getcode(self) -> int:
        return int(self._status)

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_http_sink_requires_url():
    with pytest.raises(ValueError):
        HttpJsonSink(config={})


def test_http_sink_posts_payload_with_idempotency_header(monkeypatch):
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout=0):
        captured["timeout"] = timeout
        captured["method"] = req.get_method()
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(200)

    monkeypatch.setattr(http_mod.request, "urlopen", fake_urlopen)

    sink = HttpJsonSink(
        config={
            "url": "http://example.invalid/api/events",
            "timeout_sec": 1.25,
            "retry_max_attempts": 1,
            "body": "payload",
        }
    )
    pkt = StreamPacket.new(
        kind="event",
        source_id="cam01",
        payload={"event_id": "e1", "event_type": "ZONE_INTRUSION"},
        meta={"idempotency_key": "event:cam01:e1"},
    )

    out = list(sink.process(pkt))
    assert out == []

    assert captured["timeout"] == 1.25
    assert captured["method"] == "POST"
    assert captured["body"] == {"event_id": "e1", "event_type": "ZONE_INTRUSION"}
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["idempotency-key"] == "event:cam01:e1"

    m = sink.metrics()
    assert m["posted_total"] == 1
    assert m["failed_total"] == 0
    assert m["retry_total"] == 0


def test_http_sink_retries_on_retryable_status(monkeypatch):
    calls = {"count": 0, "sleep": []}

    def fake_urlopen(_req, timeout=0):
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(503)
        return _FakeResponse(201)

    def fake_sleep(sec):
        calls["sleep"].append(sec)

    monkeypatch.setattr(http_mod.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(http_mod.time, "sleep", fake_sleep)

    sink = HttpJsonSink(
        config={
            "url": "http://example.invalid/api/events",
            "retry_max_attempts": 3,
            "retry_backoff_sec": 0.1,
            "retry_backoff_max_sec": 0.2,
        }
    )
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e1"})

    assert list(sink.process(pkt)) == []
    assert calls["count"] == 2
    assert calls["sleep"] == [0.1]

    m = sink.metrics()
    assert m["posted_total"] == 1
    assert m["failed_total"] == 0
    assert m["retry_total"] == 1


def test_http_sink_does_not_retry_on_non_retryable_4xx(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        calls["count"] += 1
        raise error.HTTPError(req.full_url, 400, "bad", {}, BytesIO(b'{"error":"bad"}'))

    monkeypatch.setattr(http_mod.request, "urlopen", fake_urlopen)

    sink = HttpJsonSink(
        config={
            "url": "http://example.invalid/api/events",
            "retry_max_attempts": 3,
            "retry_backoff_sec": 0.0,
            "retry_backoff_max_sec": 0.0,
        }
    )
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e1"})

    assert list(sink.process(pkt)) == []
    assert calls["count"] == 1

    m = sink.metrics()
    assert m["posted_total"] == 0
    assert m["failed_total"] == 1
    assert m["retry_total"] == 0


def test_http_sink_forwards_packet_on_success(monkeypatch):
    def fake_urlopen(_req, timeout=0):
        return _FakeResponse(200)

    monkeypatch.setattr(http_mod.request, "urlopen", fake_urlopen)

    sink = HttpJsonSink(
        config={
            "url": "http://example.invalid/api/events",
            "forward": True,
            "body": "packet",
            "retry_max_attempts": 1,
        }
    )
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"event_id": "e1"})

    out = list(sink.process(pkt))
    assert len(out) == 1
    assert out[0].packet_id == pkt.packet_id
    assert out[0].meta["http"]["method"] == "POST"


def test_http_sink_raises_on_non_serializable_payload(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(_req, timeout=0):
        calls["count"] += 1
        return _FakeResponse(200)

    monkeypatch.setattr(http_mod.request, "urlopen", fake_urlopen)

    sink = HttpJsonSink(config={"url": "http://example.invalid/api/events"})
    pkt = StreamPacket.new(kind="event", source_id="cam01", payload={"bad": object()})

    with pytest.raises(TypeError):
        list(sink.process(pkt))
    assert calls["count"] == 0
