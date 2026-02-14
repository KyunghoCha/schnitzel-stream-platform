# Docs: docs/implementation/60-observability/README.md
# src/ai/logging_setup.py
from __future__ import annotations

# 로깅 설정
# - plain/json 포맷 지원
# - 파일 + stdout 핸들러

from pathlib import Path
from datetime import datetime
import contextvars
import json
import logging
import os
from logging.handlers import RotatingFileHandler
import re
from typing import Any


_LOG_CONTEXT: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("ai_log_context", default={})


def set_log_context(**kwargs: Any) -> None:
    ctx = dict(_LOG_CONTEXT.get())
    ctx.update({k: v for k, v in kwargs.items() if v is not None})
    _LOG_CONTEXT.set(ctx)


def clear_log_context() -> None:
    _LOG_CONTEXT.set({})


from ai.utils.urls import mask_url


def _mask_path(path: str) -> str:
    # 홈 디렉터리 정도만 축약
    home = str(Path.home())
    if path.startswith(home):
        return path.replace(home, "~", 1)
    return path


def _sanitize_value(key: str, value: Any) -> Any:
    if not isinstance(value, str):
        return value
    key_lower = key.lower()
    if "url" in key_lower:
        return mask_url(value)
    if key_lower.endswith("_path") or key_lower.endswith("_dir") or "path" in key_lower:
        return _mask_path(value)
    return value


def _sanitize_filename(value: str) -> str:
    # 파일명으로 안전한 문자만 허용
    # - 경로 분리자/공백/특수문자 제거
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", value)
    return cleaned.strip("._-") or "unknown"


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _LOG_CONTEXT.get()
        for k, v in ctx.items():
            if k not in record.__dict__:
                record.__dict__[k] = v
        # 기본 필드 보장
        record.__dict__.setdefault("camera_id", "-")
        record.__dict__.setdefault("source_type", "-")
        record.__dict__.setdefault("event_id", "-")
        record.__dict__.setdefault("event_type", "-")
        record.__dict__.setdefault("error_code", "-")
        return True


class JsonFormatter(logging.Formatter):
    # 간단 JSON 포맷터
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # extra 필드가 있으면 포함
        for key in ("camera_id", "source_type", "event_id", "event_type", "error_code", "metrics", "heartbeat"):
            val = record.__dict__.get(key)
            if val is not None:
                if isinstance(val, dict):
                    payload[key] = {k: _sanitize_value(k, v) for k, v in val.items()}
                else:
                    payload[key] = _sanitize_value(key, val)
        return json.dumps(payload, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.__dict__.setdefault("camera_id", "-")
        record.__dict__.setdefault("source_type", "-")
        record.__dict__.setdefault("event_id", "-")
        record.__dict__.setdefault("event_type", "-")
        record.__dict__.setdefault("error_code", "-")
        return super().format(record)


def setup_logging(
    log_dir: str,
    level: str = "INFO",
    fmt: str = "plain",
    file_suffix: str | None = None,
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    safe_suffix = _sanitize_filename(file_suffix) if file_suffix else None
    suffix = f"_{safe_suffix}" if safe_suffix else ""
    log_file = Path(log_dir) / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}.log"
    # 환경변수가 있으면 파라미터보다 우선 (하위 호환)
    max_bytes = int(os.getenv("AI_LOG_MAX_BYTES", str(max_bytes)))
    backup_count = int(os.getenv("AI_LOG_BACKUP_COUNT", str(backup_count)))
    env_level = os.getenv("AI_LOG_LEVEL")
    env_fmt = os.getenv("AI_LOG_FORMAT")

    root_logger = logging.getLogger()
    # 중복 핸들러 방지: 이전에 설정된 핸들러가 있으면 제거
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    handlers: list[logging.Handler] = [
        RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"),
        logging.StreamHandler(),
    ]

    fmt = env_fmt or fmt
    if fmt == "json":
        formatter = JsonFormatter()
    else:
        formatter = PlainFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s | camera=%(camera_id)s source=%(source_type)s "
            "| event=%(event_id)s type=%(event_type)s | code=%(error_code)s"
        )

    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())

    logging.basicConfig(
        level=getattr(logging, (env_level or level).upper(), logging.INFO),
        handlers=handlers,
    )
    logging.getLogger(__name__).info(f"Logging to {log_file}")
