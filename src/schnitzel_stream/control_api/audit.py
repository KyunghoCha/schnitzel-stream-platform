from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4


ENV_AUDIT_MAX_BYTES = "SS_AUDIT_MAX_BYTES"
ENV_AUDIT_MAX_FILES = "SS_AUDIT_MAX_FILES"
DEFAULT_AUDIT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_AUDIT_MAX_FILES = 5


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


def _safe_int(raw: str, *, default: int, minimum: int) -> int:
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return int(default)
    if value < int(minimum):
        return int(minimum)
    return int(value)


def audit_max_bytes_from_env() -> int:
    raw = os.environ.get(ENV_AUDIT_MAX_BYTES, "")
    return _safe_int(raw, default=DEFAULT_AUDIT_MAX_BYTES, minimum=1024)


def audit_max_files_from_env() -> int:
    raw = os.environ.get(ENV_AUDIT_MAX_FILES, "")
    return _safe_int(raw, default=DEFAULT_AUDIT_MAX_FILES, minimum=1)


class AuditLogger:
    def __init__(self, path: Path, *, max_bytes: int | None = None, max_files: int | None = None) -> None:
        self._path = Path(path).resolve()
        self._lock = threading.Lock()
        self._max_bytes = int(max_bytes if max_bytes is not None else audit_max_bytes_from_env())
        self._max_files = int(max_files if max_files is not None else audit_max_files_from_env())
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def max_bytes(self) -> int:
        return int(self._max_bytes)

    @property
    def max_files(self) -> int:
        return int(self._max_files)

    def _rotated_path(self, index: int) -> Path:
        return Path(f"{self._path}.{int(index)}")

    def _rotate_if_needed_locked(self, *, next_line_bytes: int) -> None:
        if int(self._max_bytes) <= 0:
            return
        if not self._path.exists():
            return
        try:
            current_size = int(self._path.stat().st_size)
        except OSError:
            return
        if current_size + int(next_line_bytes) <= int(self._max_bytes):
            return

        max_files = max(1, int(self._max_files))
        backups = max_files - 1
        if backups <= 0:
            try:
                self._path.unlink()
            except OSError:
                return
            return

        # Intent: rotate newest->oldest safely on Windows by removing destination before replace.
        for idx in range(backups, 0, -1):
            src = self._path if idx == 1 else self._rotated_path(idx - 1)
            dst = self._rotated_path(idx)
            if not src.exists():
                continue
            if dst.exists():
                try:
                    dst.unlink()
                except OSError:
                    continue
            try:
                src.replace(dst)
            except OSError:
                continue

    def _read_lines_locked(self) -> list[str]:
        lines: list[str] = []
        backups = max(0, int(self._max_files) - 1)
        for idx in range(backups, 0, -1):
            path = self._rotated_path(idx)
            if not path.exists():
                continue
            try:
                lines.extend(path.read_text(encoding="utf-8").splitlines())
            except OSError:
                continue
        if self._path.exists():
            try:
                lines.extend(self._path.read_text(encoding="utf-8").splitlines())
            except OSError:
                return lines
        return lines

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
            self._rotate_if_needed_locked(next_line_bytes=len(line.encode("utf-8")) + 1)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return event

    def tail(self, *, limit: int, since: str = "") -> list[dict[str, Any]]:
        parsed_since = _parse_iso8601(since)
        rows: list[dict[str, Any]] = []
        with self._lock:
            lines = self._read_lines_locked()

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
