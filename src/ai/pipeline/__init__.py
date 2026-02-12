# Docs: docs/index.md
from __future__ import annotations

# Avoid heavy imports at package import time (e.g., cv2).
from importlib import import_module
from typing import TYPE_CHECKING

__all__ = [
    "Pipeline",
    "PipelineContext",
    "PipelineSettings",
    "load_pipeline_settings",
    "FileSource",
    "RtspSource",
    "BackendEmitter",
    "StdoutEmitter",
    "DummyEventBuilder",
    "FrameSampler",
    "FrameProcessor",
]

_EXPORTS = {
    "Pipeline": ("ai.pipeline.core", "Pipeline"),
    "PipelineContext": ("ai.pipeline.core", "PipelineContext"),
    "PipelineSettings": ("ai.pipeline.config", "PipelineSettings"),
    "load_pipeline_settings": ("ai.pipeline.config", "load_pipeline_settings"),
    "FileSource": ("ai.pipeline.sources", "FileSource"),
    "RtspSource": ("ai.pipeline.sources", "RtspSource"),
    "BackendEmitter": ("ai.pipeline.emitter", "BackendEmitter"),
    "StdoutEmitter": ("ai.pipeline.emitter", "StdoutEmitter"),
    "DummyEventBuilder": ("ai.pipeline.events", "DummyEventBuilder"),
    "FrameSampler": ("ai.pipeline.sampler", "FrameSampler"),
    "FrameProcessor": ("ai.pipeline.processor", "FrameProcessor"),
}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if not target:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = target
    module = import_module(module_name)
    return getattr(module, attr)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORTS.keys()))


if TYPE_CHECKING:  # pragma: no cover
    from ai.pipeline.core import Pipeline, PipelineContext
    from ai.pipeline.config import PipelineSettings, load_pipeline_settings
    from ai.pipeline.sources import FileSource, RtspSource
    from ai.pipeline.emitter import BackendEmitter, StdoutEmitter
    from ai.pipeline.events import DummyEventBuilder
    from ai.pipeline.sampler import FrameSampler
    from ai.pipeline.processor import FrameProcessor
