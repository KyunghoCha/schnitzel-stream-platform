from __future__ import annotations

"""
URL masking helpers.

Intent:
- Originally ported from legacy code; now fully platform-owned.
- Hide credentials in logs by default.
"""

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
