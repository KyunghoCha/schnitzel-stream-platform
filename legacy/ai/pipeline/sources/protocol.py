# Docs: docs/legacy/specs/legacy_pipeline_spec.md
from __future__ import annotations

# 프레임 소스 공통 인터페이스 (Protocol)

from typing import Any, Protocol


class FrameSource(Protocol):
    """프레임 소스 공통 인터페이스"""

    supports_reconnect: bool

    @property
    def is_live(self) -> bool:
        ...

    def read(self) -> tuple[bool, Any]:
        ...

    def release(self) -> None:
        ...

    def fps(self) -> float:
        ...
