from __future__ import annotations

import json
from urllib import error

from ai.clients.backend_api import BackendClient, BackendClientConfig


class _FakeResponse:
    def __init__(self, status: int, body: bytes = b"{}"): 
        self._status = status
        self._body = body

    def getcode(self):
        return self._status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_backend_client_no_retry_on_4xx(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        calls["count"] += 1
        raise error.HTTPError(req.full_url, 400, "bad", {}, None)

    monkeypatch.setattr("ai.clients.backend_api.request.urlopen", fake_urlopen)

    client = BackendClient(BackendClientConfig(post_url="http://example", retry_max_attempts=3))
    ok = client.post_event({"event_id": "e1"})
    assert ok is False
    assert calls["count"] == 1


def test_backend_client_retries_on_5xx(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        calls["count"] += 1
        if calls["count"] < 3:
            raise error.HTTPError(req.full_url, 500, "oops", {}, None)
        return _FakeResponse(200, b"{}")

    monkeypatch.setattr("ai.clients.backend_api.request.urlopen", fake_urlopen)

    client = BackendClient(BackendClientConfig(post_url="http://example", retry_max_attempts=3))
    ok = client.post_event({"event_id": "e1"})
    assert ok is True
    assert calls["count"] == 3
