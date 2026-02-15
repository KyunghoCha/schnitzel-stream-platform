# Docs: docs/legacy/design/multimodal_pipeline_design.md
"""
센서 소스 패키지 (P1 런타임)

- SensorSource: 센서 입력 공통 프로토콜
- load_sensor_source: 커스텀 센서 플러그인 로더(module:ClassName)
- SensorRuntime: 센서 수집 워커 + 시간창 매칭
- MultiSensorRuntime: 다중 센서 런타임 합성
- SensorAwareEventBuilder: 이벤트 빌더 센서 주입 래퍼
- SensorEventBuilder: 독립 sensor_event 생성기
- FusionEngine: 시간창 기반 센서 융합 유틸
"""
from __future__ import annotations

from ai.pipeline.sensors.builder import SensorAwareEventBuilder, SensorEventBuilder
from ai.pipeline.sensors.fusion import FusionEngine
from ai.pipeline.sensors.loader import load_sensor_source
from ai.pipeline.sensors.protocol import SensorSource
from ai.pipeline.sensors.runtime import MultiSensorRuntime, SensorRuntime, SensorRuntimeLike

__all__ = [
    "SensorSource",
    "load_sensor_source",
    "SensorRuntime",
    "SensorRuntimeLike",
    "MultiSensorRuntime",
    "SensorAwareEventBuilder",
    "SensorEventBuilder",
    "FusionEngine",
]
