from __future__ import annotations

from http import HTTPStatus
from urllib import error

from ai.clients.backend_api import BackendClient, BackendClientConfig


class _FakeResponse:
    def __init__(self, status: int, body: bytes = b"{}"):
        self._status = status
        self._body = body

    def getcode(self) -> int:
        return self._status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


# 4xx/5xx retry policy is covered by unit tests (test_backend_client.py).


def test_backend_policy_non_2xx_response(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        calls["count"] += 1
        return _FakeResponse(HTTPStatus.ACCEPTED, b"{\"ok\": true}")

    monkeypatch.setattr("ai.clients.backend_api.request.urlopen", fake_urlopen)

    client = BackendClient(BackendClientConfig(post_url="http://example", retry_max_attempts=2))
    ok = client.post_event({"event_id": "e1"})
    assert ok is True
    assert calls["count"] == 1


def test_backend_policy_timeout_retries(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout=0):
        calls["count"] += 1
        raise TimeoutError("timeout")

    monkeypatch.setattr("ai.clients.backend_api.request.urlopen", fake_urlopen)

    client = BackendClient(BackendClientConfig(post_url="http://example", retry_max_attempts=2))
    ok = client.post_event({"event_id": "e1"})
    assert ok is False
    assert calls["count"] == 2
