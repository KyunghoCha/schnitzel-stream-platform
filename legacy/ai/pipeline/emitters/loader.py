from __future__ import annotations

import importlib

from ai.pipeline.emitters.protocol import EventEmitter


def load_event_emitter(path: str) -> EventEmitter:
    """module:Name 경로에서 커스텀 EventEmitter를 로드한다.

    - Name이 class면 인자 없이 인스턴스화
    - Name이 함수면 호출 결과를 emitter로 사용
    - 객체는 emit(payload)->bool, close()를 제공해야 한다.
    """
    if ":" not in path:
        raise ValueError("event emitter path must be in form 'module:ClassName'")

    module_path, name = path.split(":", 1)
    module = importlib.import_module(module_path)
    target = getattr(module, name, None)
    if target is None:
        raise ImportError(f"event emitter target not found: {path}")

    try:
        instance = target() if callable(target) else target
    except TypeError as exc:
        raise TypeError(
            "event emitter target must be a no-arg class/function returning an emitter",
        ) from exc

    if not callable(getattr(instance, "emit", None)) or not callable(getattr(instance, "close", None)):
        raise TypeError(f"loaded object is not an EventEmitter: {path}")
    return instance
