from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso8601(raw: str) -> datetime | None:
    txt = str(raw or "").strip()
    if not txt:
        return None
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    ts: str
    actor: str
    action: str
    target: str
    status: str
    reason: str
    request_id: str
    meta: dict[str, Any]


class AuditLogger:
    def __init__(self, path: Path) -> None:
        self._path = Path(path).resolve()
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def append(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        status: str,
        reason: str,
        request_id: str,
        meta: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid4()),
            ts=_utc_now().isoformat(),
            actor=str(actor),
            action=str(action),
            target=str(target),
            status=str(status),
            reason=str(reason),
            request_id=str(request_id),
            meta=dict(meta or {}),
        )
        line = json.dumps(event.__dict__, ensure_ascii=False)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return event

    def tail(self, *, limit: int, since: str = "") -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        parsed_since = _parse_iso8601(since)
        rows: list[dict[str, Any]] = []
        with self._lock:
            lines = self._path.read_text(encoding="utf-8").splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if parsed_since is not None:
                row_ts = _parse_iso8601(str(obj.get("ts", "")))
                if row_ts is None or row_ts < parsed_since:
                    continue
            rows.append(obj)

        if limit <= 0:
            return rows
        return rows[-int(limit) :]
