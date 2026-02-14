from __future__ import annotations

from typing import Any, Protocol


class EventEmitter(Protocol):
    # 이벤트 전송 인터페이스
    def emit(self, payload: dict[str, Any]) -> bool:
        ...

    def close(self) -> None:
        ...
