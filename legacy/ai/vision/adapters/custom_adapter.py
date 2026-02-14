# Docs: docs/specs/model_interface.md, docs/ops/ai/model_yolo_run.md
# 사용자 정의 모델 연결을 위한 최소 템플릿 어댑터.
from __future__ import annotations

from typing import Any

from ai.pipeline.model_adapter import ModelAdapter


class CustomModelAdapter(ModelAdapter):
    def __init__(self) -> None:
        # 의도: 템플릿 어댑터의 무의미한 가짜 이벤트 방출을 방지하기 위해
        # 구현 전에는 즉시 실패시킨다. 테스트는 AI_MODEL_MODE=mock를 사용.
        raise RuntimeError(
            "CustomModelAdapter is a template. Implement this adapter before real-mode use, "
            "or set AI_MODEL_ADAPTER to a concrete adapter "
            "(e.g., ai.vision.adapters.yolo_adapter:YOLOAdapter).",
        )

    def infer(self, frame: Any) -> list[dict[str, Any]]:
        # 정상 경로에서는 __init__에서 실패하므로 실행되지 않는다.
        raise NotImplementedError(
            "Implement infer() to return detection payloads matching model interface contract.",
        )
