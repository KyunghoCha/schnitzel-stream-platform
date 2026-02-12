from __future__ import annotations

import threading

from ai.clients.backend_api import BackendClientConfig
from ai.pipeline.emitters import BackendEmitter


def test_backend_emitter_reports_delivery_success(monkeypatch):
    class _OkClient:
        def __init__(self, _config):
            pass

        def post_event(self, payload):
            return payload["event_id"] == "e1"

    monkeypatch.setattr("ai.pipeline.emitters.backend.BackendClient", _OkClient)

    results: list[bool] = []
    done = threading.Event()

    def _on_delivery(ok: bool) -> None:
        results.append(ok)
        done.set()

    emitter = BackendEmitter(
        BackendClientConfig(post_url="http://example"),
        delivery_callback=_on_delivery,
    )
    try:
        assert emitter.emit({"event_id": "e1"}) is True
        assert done.wait(1.0)
        assert results == [True]
    finally:
        emitter.close()


def test_backend_emitter_reports_delivery_failure_on_exception(monkeypatch):
    class _FailClient:
        def __init__(self, _config):
            pass

        def post_event(self, payload):
            raise RuntimeError(f"boom:{payload.get('event_id')}")

    monkeypatch.setattr("ai.pipeline.emitters.backend.BackendClient", _FailClient)

    results: list[bool] = []
    done = threading.Event()

    def _on_delivery(ok: bool) -> None:
        results.append(ok)
        done.set()

    emitter = BackendEmitter(
        BackendClientConfig(post_url="http://example"),
        delivery_callback=_on_delivery,
    )
    try:
        assert emitter.emit({"event_id": "e2"}) is True
        assert done.wait(1.0)
        assert results == [False]
    finally:
        emitter.close()
