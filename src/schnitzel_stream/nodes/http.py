from __future__ import annotations

"""
HTTP sink node plugins.

Intent:
- Provide a transport-agnostic HTTP sink for v2 graphs without coupling runtime core to backend schema.
- Keep delivery semantics explicit in config (idempotency header + retry policy).
"""

from dataclasses import replace
import json
import time
from typing import Any, Iterable
from urllib import error, request

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.utils.urls import mask_url


class HttpJsonSink:
    """POST packets to an HTTP endpoint.

    Config:
    - url: str (required)
    - method: str (default: "POST")
    - timeout_sec: float (default: 3.0)
    - body: "payload"|"packet" (default: "payload")
      - payload: send `packet.payload` as JSON
      - packet: send `{packet_id, ts, kind, source_id, payload, meta}` envelope
    - headers: dict[str, str] (optional; additional HTTP headers)
    - idempotency_header: str (default: "Idempotency-Key"; empty to disable)
    - retry_max_attempts: int (default: 3; must be >= 1)
    - retry_backoff_sec: float (default: 1.0)
    - retry_backoff_max_sec: float (default: 10.0)
    - retry_on_status: list[int] (default: [408, 409, 425, 429, 500, 502, 503, 504])
    - forward: bool (default: false; emit input packet downstream on success)
    - raise_on_fail: bool (default: false; raise RuntimeError after retry exhaustion)
    """

    INPUT_KINDS = {"*"}
    OUTPUT_KINDS = {"*"}
    REQUIRES_PORTABLE_PAYLOAD = True

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})

        url = cfg.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("HttpJsonSink requires config.url")

        self._node_id = str(node_id or "http_sink")
        self._url = str(url.strip())
        self._method = str(cfg.get("method", "POST")).strip().upper() or "POST"

        self._timeout_sec = float(cfg.get("timeout_sec", 3.0))

        body_mode = str(cfg.get("body", "payload")).strip().lower() or "payload"
        if body_mode not in ("payload", "packet"):
            raise ValueError("HttpJsonSink config.body must be 'payload' or 'packet'")
        self._body_mode = body_mode

        hdrs_raw = cfg.get("headers", {})
        if hdrs_raw is None:
            hdrs_raw = {}
        if not isinstance(hdrs_raw, dict):
            raise ValueError("HttpJsonSink config.headers must be a mapping")
        self._headers = {str(k): str(v) for k, v in hdrs_raw.items()}

        self._idempotency_header = str(cfg.get("idempotency_header", "Idempotency-Key"))

        self._retry_max_attempts = int(cfg.get("retry_max_attempts", 3))
        if self._retry_max_attempts < 1:
            raise ValueError("HttpJsonSink config.retry_max_attempts must be >= 1")

        self._retry_backoff_sec = max(0.0, float(cfg.get("retry_backoff_sec", 1.0)))
        self._retry_backoff_max_sec = max(
            self._retry_backoff_sec,
            float(cfg.get("retry_backoff_max_sec", 10.0)),
        )

        retry_on_status_raw = cfg.get("retry_on_status")
        if retry_on_status_raw is None:
            retry_on_status_raw = [408, 409, 425, 429, 500, 502, 503, 504]
        if not isinstance(retry_on_status_raw, list):
            raise ValueError("HttpJsonSink config.retry_on_status must be a list[int]")
        self._retry_on_status = {
            int(v)
            for v in retry_on_status_raw
            if isinstance(v, (int, str)) and str(v).strip()
        }

        self._forward = bool(cfg.get("forward", False))
        self._raise_on_fail = bool(cfg.get("raise_on_fail", False))

        self._posted_total = 0
        self._failed_total = 0
        self._retry_total = 0

    def _build_body(self, packet: StreamPacket) -> Any:
        if self._body_mode == "packet":
            return {
                "packet_id": packet.packet_id,
                "ts": packet.ts,
                "kind": packet.kind,
                "source_id": packet.source_id,
                "payload": packet.payload,
                "meta": dict(packet.meta),
            }
        return packet.payload

    def _is_retryable_status(self, status: int) -> bool:
        return int(status) in self._retry_on_status

    def _sleep_backoff(self, backoff: float) -> float:
        if backoff > 0:
            time.sleep(backoff)
        if backoff <= 0:
            return 0.0
        return min(self._retry_backoff_max_sec, backoff * 2.0)

    def _headers_for_packet(self, packet: StreamPacket) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        if self._idempotency_header.strip():
            idem_key = str(packet.meta.get("idempotency_key") or packet.packet_id)
            # Intent: always attach a stable delivery key so at-least-once sinks can dedup safely.
            headers[self._idempotency_header] = idem_key
        return headers

    def _post_once(self, *, data: bytes, headers: dict[str, str]) -> int:
        req = request.Request(self._url, data=data, headers=headers, method=self._method)
        with request.urlopen(req, timeout=self._timeout_sec) as resp:
            return int(resp.getcode())

    def _post_with_retry(self, packet: StreamPacket, *, data: bytes, headers: dict[str, str]) -> bool:
        backoff = self._retry_backoff_sec

        for attempt in range(1, self._retry_max_attempts + 1):
            try:
                status = self._post_once(data=data, headers=headers)
                if 200 <= status < 300:
                    return True
                if not self._is_retryable_status(status):
                    break
            except error.HTTPError as exc:
                status = int(getattr(exc, "code", 0) or 0)
                if not self._is_retryable_status(status):
                    break
            except (error.URLError, TimeoutError):
                status = 0

            if attempt >= self._retry_max_attempts:
                break
            self._retry_total += 1
            backoff = self._sleep_backoff(backoff)

        self._failed_total += 1
        if self._raise_on_fail:
            raise RuntimeError(f"http delivery failed: {mask_url(self._url)}")
        return False

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        body = self._build_body(packet)
        try:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        except TypeError as exc:
            raise TypeError(f"{self._node_id}: payload is not JSON-serializable") from exc

        headers = self._headers_for_packet(packet)
        ok = self._post_with_retry(packet, data=data, headers=headers)
        if not ok:
            return []

        self._posted_total += 1
        if not self._forward:
            return []

        meta = dict(packet.meta)
        meta["http"] = {
            "url": mask_url(self._url),
            "method": self._method,
            "node_id": self._node_id,
        }
        return [replace(packet, meta=meta)]

    def metrics(self) -> dict[str, int]:
        return {
            "posted_total": int(self._posted_total),
            "failed_total": int(self._failed_total),
            "retry_total": int(self._retry_total),
        }

    def close(self) -> None:
        return
