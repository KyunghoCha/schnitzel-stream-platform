# Docs: docs/legacy/specs/legacy_pipeline_spec.md
from __future__ import annotations

# 더미 백엔드 서버
# - POST /api/events 수신
# - stdout 또는 jsonl로 기록

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class _Handler(BaseHTTPRequestHandler):
    server_version = "MockBackend/0.1"

    def _send_json(self, status: int, body: dict) -> None:
        # 공통 JSON 응답
        data = json.dumps(body, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        # 이벤트 수신 엔드포인트
        if self.path != "/api/events":
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            self._send_json(400, {"ok": False, "error": "invalid Content-Length"})
            return
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "invalid json"})
            return

        # optional 파일 기록
        sink = getattr(self.server, "sink", None)
        if sink is not None:
            sink.write(json.dumps(payload, ensure_ascii=True) + "\n")
            sink.flush()
        logger.info("event=%s", payload)
        self._send_json(200, {"ok": True})


def run(host: str, port: int, output_jsonl: str | None = None) -> None:
    # mock backend 실행
    sink = None
    if output_jsonl:
        Path(output_jsonl).parent.mkdir(parents=True, exist_ok=True)
        sink = open(output_jsonl, "a", encoding="utf-8")

    server = HTTPServer((host, port), _Handler)
    server.sink = sink  # type: ignore[attr-defined]

    logger.info("mock backend listening on http://%s:%s", host, port)
    try:
        server.serve_forever()
    finally:
        if sink is not None:
            sink.close()


if __name__ == "__main__":
    # 단독 실행 시 기본 포트 8080
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    port = int(os.environ.get("MOCK_BACKEND_PORT", "8080"))
    host = os.environ.get("MOCK_BACKEND_HOST", "127.0.0.1")
    run(host, port, None)
