from __future__ import annotations

import importlib

from ai.pipeline.sensors.protocol import SensorSource


def load_sensor_source(path: str) -> SensorSource:
    """module:Name 경로에서 커스텀 SensorSource를 로드한다.

    - Name이 class면 인자 없이 인스턴스화
    - Name이 함수면 호출 결과를 source로 사용
    - 객체는 SensorSource 프로토콜(read/release/sensor_type)을 만족해야 한다.
    """
    if ":" not in path:
        raise ValueError("sensor adapter path must be in form 'module:ClassName'")

    module_path, name = path.split(":", 1)
    module = importlib.import_module(module_path)
    target = getattr(module, name, None)
    if target is None:
        raise ImportError(f"sensor adapter target not found: {path}")

    try:
        instance = target() if callable(target) else target
    except TypeError as exc:
        raise TypeError(
            "sensor adapter target must be a no-arg class/function returning a SensorSource",
        ) from exc

    has_required = (
        callable(getattr(instance, "read", None))
        and callable(getattr(instance, "release", None))
        and hasattr(instance, "sensor_type")
    )
    if not has_required:
        raise TypeError(f"loaded object is not a SensorSource: {path}")
    return instance
