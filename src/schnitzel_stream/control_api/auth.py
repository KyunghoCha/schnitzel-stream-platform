from __future__ import annotations

import os
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, Request, status


def configured_token() -> str:
    return os.environ.get("SS_CONTROL_API_TOKEN", "").strip()


def security_mode() -> str:
    token = configured_token()
    return "local+bearer" if token else "local-only"


def request_identity(request: Request) -> Tuple[str, str]:
    req_id = request.headers.get("X-Request-Id", "").strip() or str(uuid4())
    token = configured_token()
    client_host = (request.client.host if request.client else "") or ""
    is_local_client = client_host in {"127.0.0.1", "::1", "localhost", "testclient"}

    if token:
        auth = request.headers.get("Authorization", "").strip()
        prefix = "Bearer "
        if not auth.startswith(prefix):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
        raw = auth[len(prefix) :].strip()
        if raw != token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid bearer token")
        return "token", req_id

    # Intent: default local-only mode prevents accidental remote control exposure without explicit token setup.
    if not is_local_client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="remote access disabled in local-only mode")
    return "local", req_id
