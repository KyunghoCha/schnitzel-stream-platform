from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from ai.rules.zones import ZoneCache, load_zones


class _ZonesHandler(BaseHTTPRequestHandler):
    calls = 0

    def do_GET(self):
        _ZonesHandler.calls += 1
        if _ZonesHandler.calls == 1:
            payload = [
                {
                    "zone_id": "Z1",
                    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
                    "enabled": True,
                }
            ]
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(500)
        self.end_headers()

    def log_message(self, fmt: str, *args) -> None:  # pragma: no cover
        return


def test_zones_api_fallback_to_cached_on_error():
    server = HTTPServer(("127.0.0.1", 0), _ZonesHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    cache = ZoneCache(ttl_sec=0.0)
    api_cfg = {
        "base_url": f"http://127.0.0.1:{port}",
        "get_path_template": "/api/sites/{site_id}/cameras/{camera_id}/zones",
        "timeout_sec": 1.0,
    }

    try:
        zones_first = load_zones(
            source="api",
            site_id="S001",
            camera_id="cam01",
            api_cfg=api_cfg,
            file_path=None,
            cache=cache,
        )
        assert zones_first and zones_first[0]["zone_id"] == "Z1"

        zones_second = load_zones(
            source="api",
            site_id="S001",
            camera_id="cam01",
            api_cfg=api_cfg,
            file_path=None,
            cache=cache,
        )
        assert zones_second == zones_first
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)
