from __future__ import annotations

import os
from typing import Literal, Tuple
from uuid import uuid4

from fastapi import HTTPException, Request, status


ENV_CONTROL_API_TOKEN = "SS_CONTROL_API_TOKEN"
ENV_ALLOW_LOCAL_MUTATIONS = "SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS"

AccessMode = Literal["read", "mutate"]


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "y", "on"}


def configured_token() -> str:
    return os.environ.get(ENV_CONTROL_API_TOKEN, "").strip()


def security_mode() -> str:
    token = configured_token()
    return "local+bearer" if token else "local-only"


def local_mutation_override_enabled() -> bool:
    # Intent: temporary one-cycle compatibility switch for local labs before strict mutation auth is fully adopted.
    return _env_flag(ENV_ALLOW_LOCAL_MUTATIONS, default=False)


def mutation_auth_mode() -> str:
    token = configured_token()
    if token:
        return "global_bearer"
    if local_mutation_override_enabled():
        return "local_override"
    return "bearer_required_for_mutation"


def request_identity(request: Request, *, mode: AccessMode = "read") -> Tuple[str, str]:
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

    if mode == "mutate" and not local_mutation_override_enabled():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer token required for mutating endpoint in local-only mode",
        )
    return "local", req_id
