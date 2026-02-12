from __future__ import annotations

import importlib

from ai.pipeline.sources.protocol import FrameSource


def load_frame_source(path: str) -> FrameSource:
    """module:Name 경로에서 커스텀 FrameSource를 로드한다.

    - Name이 class면 인자 없이 인스턴스화
    - Name이 함수면 호출 결과를 source로 사용
    - 객체는 FrameSource 프로토콜(read/release/fps/is_live)을 만족해야 한다.
    """
    if ":" not in path:
        raise ValueError("source adapter path must be in form 'module:ClassName'")

    module_path, name = path.split(":", 1)
    module = importlib.import_module(module_path)
    target = getattr(module, name, None)
    if target is None:
        raise ImportError(f"source adapter target not found: {path}")

    try:
        instance = target() if callable(target) else target
    except TypeError as exc:
        raise TypeError(
            "source adapter target must be a no-arg class/function returning a FrameSource",
        ) from exc

    has_required = (
        callable(getattr(instance, "read", None))
        and callable(getattr(instance, "release", None))
        and callable(getattr(instance, "fps", None))
        and hasattr(instance, "is_live")
    )
    if not has_required:
        raise TypeError(f"loaded object is not a FrameSource: {path}")
    return instance
