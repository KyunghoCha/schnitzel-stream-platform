# Docs: docs/legacy/design/multimodal_pipeline_design.md
from __future__ import annotations

from typing import Any, Protocol


class SensorSource(Protocol):
    """센서 소스 공통 인터페이스."""

    supports_reconnect: bool

    @property
    def sensor_type(self) -> str:
        ...

    def read(self) -> tuple[bool, Any]:
        ...

    def release(self) -> None:
        ...
