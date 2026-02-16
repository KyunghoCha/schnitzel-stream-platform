from __future__ import annotations

"""Minimal mock backend for local sink/integration tests.

Intent:
- Provide a small platform-owned mock event receiver for local validation.
- Keep behavior intentionally small: accept `POST /api/events`, print payload, return 200.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/events":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            payload = {"raw": body.decode("utf-8", errors="replace")}

        print(f"event={json.dumps(payload, ensure_ascii=False)}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, _format: str, *_args: object) -> None:
        # Keep stdout signal clean for scripts that parse `event=` lines.
        return


def main() -> None:
    host = os.environ.get("MOCK_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("MOCK_BACKEND_PORT", "18080"))

    server = HTTPServer((host, port), _Handler)
    print(f"mock backend listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
