# Docs: docs/implementation/60-observability/README.md
from __future__ import annotations

# 안전한 로깅을 위한 URL 마스킹 (사용자 정보의 자격 증명 숨김).

from urllib.parse import urlparse, urlunparse


def mask_url(url: str) -> str:
    if "://" not in url:
        return url
    try:
        parts = urlparse(url)
        if not parts.username and not parts.password:
            return url
        netloc = parts.hostname or ""
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
        if parts.username:
            user = parts.username
            if parts.password:
                user = f"{parts.username}:***"
            netloc = f"{user}@{netloc}"
        return urlunparse((parts.scheme, netloc, parts.path, parts.params, parts.query, parts.fragment))
    except Exception:
        return url
