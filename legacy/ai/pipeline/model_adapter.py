# Docs: docs/specs/model_interface.md
from __future__ import annotations

# 모델 어댑터 인터페이스 (스켈레톤)

import importlib
import logging
from typing import Protocol, Any


class ModelAdapter(Protocol):
    # 모델 추론 결과를 detection 리스트로 반환
    # - 각 detection은 model_interface.md의 최소 키를 포함해야 함
    def infer(self, frame: Any) -> list[dict[str, Any]]:
        ...


logger = logging.getLogger(__name__)


_MAX_CONSECUTIVE_FAILURES = 10  # 연속 실패 시 경고 임계값


class CompositeModelAdapter(ModelAdapter):
    # 여러 어댑터 결과를 합산하는 래퍼
    def __init__(self, adapters: list[ModelAdapter]) -> None:
        self._adapters = adapters
        self._consecutive_failures: dict[int, int] = {}

    def infer(self, frame: Any) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        for idx, adapter in enumerate(self._adapters):
            try:
                dets = adapter.infer(frame)
                self._consecutive_failures[idx] = 0
            except Exception as exc:
                count = self._consecutive_failures.get(idx, 0) + 1
                self._consecutive_failures[idx] = count
                if count == 1 or count % _MAX_CONSECUTIVE_FAILURES == 0:
                    logger.warning(
                        "model adapter inference failed (consecutive=%d): %s", count, exc,
                    )
                continue
            if dets is None:
                continue
            if isinstance(dets, dict):
                merged.append(dets)
                continue
            if isinstance(dets, list):
                merged.extend([d for d in dets if isinstance(d, dict)])
                continue
            logger.warning("model adapter returned unsupported type: %s", type(dets).__name__)
        return merged


def _load_single_adapter(path: str) -> ModelAdapter:
    if ":" not in path:
        raise ValueError("model adapter path must be in form 'module:ClassName'")
    module_path, class_name = path.split(":", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ImportError(f"adapter class not found: {path}")
    return cls()


def load_model_adapter(path: str) -> ModelAdapter:
    # "module:ClassName" 형식 또는 쉼표로 구분된 목록에서 어댑터 로드
    paths = [p.strip() for p in path.split(",") if p.strip()]
    if not paths:
        raise ValueError("model adapter path must not be empty")
    if len(paths) == 1:
        return _load_single_adapter(paths[0])
    adapters = [_load_single_adapter(p) for p in paths]
    return CompositeModelAdapter(adapters)
