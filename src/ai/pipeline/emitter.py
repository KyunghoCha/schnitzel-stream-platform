# Docs: docs/implementation/50-backend-integration/README.md
from __future__ import annotations

# Backward-compatibility shim.
# Prefer importing from ai.pipeline.emitters.

from ai.pipeline.emitters import BackendEmitter, EventEmitter, FileEmitter, StdoutEmitter, load_event_emitter

__all__ = [
    "EventEmitter",
    "load_event_emitter",
    "BackendEmitter",
    "StdoutEmitter",
    "FileEmitter",
]
