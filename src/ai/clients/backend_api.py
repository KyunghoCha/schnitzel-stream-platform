# Docs: docs/implementation/50-backend-integration/README.md
from __future__ import annotations

# 백엔드 이벤트 전송 클라이언트
# - HTTP POST /api/events
# - 재시도/백오프 포함

from dataclasses import dataclass
import json
import logging
import time
from typing import Any
from urllib import request, error

logger = logging.getLogger(__name__)


def _truncate_body(data: bytes | None, limit: int = 200) -> str:
    if not data:
        return ""
    text = data.decode("utf-8", errors="replace")
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


@dataclass
class BackendClientConfig:
    # 백엔드 통신 설정
    post_url: str
    timeout_sec: float = 3.0
    retry_max_attempts: int = 3
    retry_backoff_sec: float = 1.0


class BackendClient:
    def __init__(self, config: BackendClientConfig) -> None:
        self.config = config

    def post_event(self, payload: dict[str, Any]) -> bool:
        # payload를 JSON으로 직렬화하여 백엔드에 전송
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        extra = {
            "camera_id": payload.get("camera_id"),
            "event_id": payload.get("event_id"),
            "event_type": payload.get("event_type"),
        }

        last_error: Exception | None = None
        for attempt in range(1, self.config.retry_max_attempts + 1):
            try:
                # 요청 생성 및 전송
                req = request.Request(self.config.post_url, data=data, headers=headers, method="POST")
                with request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                    status = resp.getcode()
                    if 200 <= status < 300:
                        return True
                    body = _truncate_body(resp.read())
                    logger.warning(
                        "Backend returned non-2xx: status=%s body=%s",
                        status,
                        body,
                        extra={**extra, "error_code": "BACKEND_NON_2XX"},
                    )
            except error.HTTPError as exc:
                last_error = exc
                status = getattr(exc, "code", None)
                body = _truncate_body(exc.read())
                # 4xx는 재시도하지 않음 (payload 문제 가능성)
                if status is not None and 400 <= status < 500:
                    logger.error(
                        "Backend returned 4xx, dropping: status=%s body=%s",
                        status,
                        body,
                        extra={**extra, "error_code": "BACKEND_NON_2XX"},
                    )
                    break
                logger.warning(
                    "Backend post failed (attempt %s/%s): %s",
                    attempt,
                    self.config.retry_max_attempts,
                    exc,
                    extra={**extra, "error_code": "BACKEND_POST_FAILED"},
                )
            except (error.URLError, TimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "Backend post failed (attempt %s/%s): %s",
                    attempt,
                    self.config.retry_max_attempts,
                    exc,
                    extra={**extra, "error_code": "BACKEND_POST_FAILED"},
                )

            if attempt < self.config.retry_max_attempts:
                # 재시도 전 백오프
                time.sleep(self.config.retry_backoff_sec)

        if last_error:
            logger.error(
                "Backend post failed after retries: %s",
                last_error,
                extra={**extra, "error_code": "BACKEND_POST_GIVEUP"},
            )
        return False
