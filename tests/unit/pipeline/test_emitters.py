"""EventEmitter 구현체 (StdoutEmitter, FileEmitter) 단위 테스트."""
from __future__ import annotations

import json
from pathlib import Path
import types
import sys

import pytest

import ai.pipeline.emitter as legacy_emitters
from ai.pipeline.emitter import FileEmitter, StdoutEmitter, load_event_emitter


def test_stdout_emitter_returns_true():
    emitter = StdoutEmitter()
    assert emitter.emit({"event_id": "e1"}) is True
    emitter.close()


def test_file_emitter_writes_jsonl(tmp_path: Path):
    out = tmp_path / "events.jsonl"
    emitter = FileEmitter(str(out))
    emitter.emit({"event_id": "e1", "msg": "hello"})
    emitter.emit({"event_id": "e2", "msg": "world"})
    emitter.close()

    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["event_id"] == "e1"
    assert json.loads(lines[1])["event_id"] == "e2"


def test_file_emitter_context_manager(tmp_path: Path):
    out = tmp_path / "ctx.jsonl"
    with FileEmitter(str(out)) as emitter:
        emitter.emit({"event_id": "ctx1"})
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_file_emitter_creates_parent_dirs(tmp_path: Path):
    out = tmp_path / "sub" / "deep" / "events.jsonl"
    emitter = FileEmitter(str(out))
    emitter.emit({"event_id": "nested"})
    emitter.close()
    assert out.exists()


def test_load_event_emitter_from_class(monkeypatch):
    module_name = "tests.fake_emitter_module_class"
    module = types.ModuleType(module_name)

    class _Emitter:
        def emit(self, payload):
            return True

        def close(self):
            return None

    module.CustomEmitter = _Emitter
    monkeypatch.setitem(sys.modules, module_name, module)

    emitter = load_event_emitter(f"{module_name}:CustomEmitter")
    assert emitter.emit({"event_id": "x"}) is True
    emitter.close()


def test_load_event_emitter_rejects_non_emitter(monkeypatch):
    module_name = "tests.fake_emitter_module_bad"
    module = types.ModuleType(module_name)

    class _Bad:
        pass

    module.BadEmitter = _Bad
    monkeypatch.setitem(sys.modules, module_name, module)

    with pytest.raises(TypeError, match="not an EventEmitter"):
        load_event_emitter(f"{module_name}:BadEmitter")


def test_legacy_emitter_module_reexports_modern_symbols():
    from ai.pipeline.emitters import StdoutEmitter as ModernStdoutEmitter

    assert legacy_emitters.StdoutEmitter is ModernStdoutEmitter
