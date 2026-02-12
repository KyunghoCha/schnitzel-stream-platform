"""apply_env_overrides 단위 테스트."""
from __future__ import annotations

from typing import Any

import pytest

from ai.config import apply_env_overrides, _coerce_env_value


def _get_by_path(obj: dict[str, Any], path: tuple[str, ...]) -> Any:
    cur: Any = obj
    for key in path:
        cur = cur[key]
    return cur


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("42", 42),
        ("-5", -5),
        ("3.14", 3.14),
        ("-0.5", -0.5),
    ],
)
def test_coerce_number(raw: str, expected: int | float):
    assert _coerce_env_value(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True),
        ("False", False),
    ],
)
def test_coerce_bool(raw: str, expected: bool):
    assert _coerce_env_value(raw) is expected


def test_coerce_str():
    assert _coerce_env_value("hello") == "hello"


def test_override_log_rotation(monkeypatch):
    monkeypatch.setenv("AI_LOG_MAX_BYTES", "5000000")
    monkeypatch.setenv("AI_LOG_BACKUP_COUNT", "3")
    cfg = {"logging": {"level": "INFO"}}
    result = apply_env_overrides(cfg)
    assert result["logging"]["max_bytes"] == 5000000
    assert result["logging"]["backup_count"] == 3


@pytest.mark.parametrize(
    ("env_key", "env_value", "cfg", "path", "expected"),
    [
        (
            "AI_EVENTS_POST_URL",
            "http://test:9090/api/events",
            {"events": {"post_url": "http://old:8080/api/events"}},
            ("events", "post_url"),
            "http://test:9090/api/events",
        ),
        (
            "AI_MODEL_ADAPTER",
            "ai.vision.adapters.yolo_adapter:YOLOAdapter",
            {"model": {"mode": "real"}},
            ("model", "adapter"),
            "ai.vision.adapters.yolo_adapter:YOLOAdapter",
        ),
        (
            "AI_EVENTS_EMITTER_ADAPTER",
            "pkg.custom:MyEmitter",
            {"events": {"post_url": "http://x"}},
            ("events", "emitter_adapter"),
            "pkg.custom:MyEmitter",
        ),
        (
            "AI_SOURCE_ADAPTER",
            "pkg.sources:MySource",
            {"source": {"type": "plugin"}},
            ("source", "adapter"),
            "pkg.sources:MySource",
        ),
        (
            "AI_SOURCE_TYPE",
            "plugin",
            {"source": {"type": "file"}},
            ("source", "type"),
            "plugin",
        ),
        (
            "AI_LOG_LEVEL",
            "DEBUG",
            {"logging": {"level": "INFO"}},
            ("logging", "level"),
            "DEBUG",
        ),
        (
            "AI_SENSOR_ADAPTER",
            "pkg.sensors:MySensor",
            {"sensor": {"enabled": True}},
            ("sensor", "adapter"),
            "pkg.sensors:MySensor",
        ),
        (
            "AI_SENSOR_ADAPTERS",
            "pkg.sensors:Front,pkg.sensors:Rear",
            {"sensor": {"enabled": True}},
            ("sensor", "adapters"),
            "pkg.sensors:Front,pkg.sensors:Rear",
        ),
        (
            "AI_SENSOR_QUEUE_SIZE",
            "512",
            {"sensor": {"queue_size": 256}},
            ("sensor", "queue_size"),
            512,
        ),
        (
            "AI_SENSOR_ENABLED",
            "true",
            {"sensor": {"enabled": False}},
            ("sensor", "enabled"),
            True,
        ),
        (
            "AI_SENSOR_EMIT_EVENTS",
            "true",
            {"sensor": {"emit_events": False}},
            ("sensor", "emit_events"),
            True,
        ),
        (
            "AI_SENSOR_EMIT_FUSED_EVENTS",
            "true",
            {"sensor": {"emit_fused_events": False}},
            ("sensor", "emit_fused_events"),
            True,
        ),
    ],
)
def test_override_single_env(
    monkeypatch,
    env_key: str,
    env_value: str,
    cfg: dict[str, Any],
    path: tuple[str, ...],
    expected: Any,
) -> None:
    monkeypatch.setenv(env_key, env_value)
    result = apply_env_overrides(cfg)
    got = _get_by_path(result, path)
    if isinstance(expected, bool):
        assert got is expected
    else:
        assert got == expected


def test_no_override_when_absent():
    cfg = {"events": {"post_url": "http://keep:8080/api"}}
    result = apply_env_overrides(cfg)
    assert result["events"]["post_url"] == "http://keep:8080/api"
