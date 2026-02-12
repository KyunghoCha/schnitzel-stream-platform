from __future__ import annotations

import sys
import types

import pytest

from ai.pipeline.sources import load_frame_source


def test_load_frame_source_from_class(monkeypatch):
    module_name = "tests.fake_source_module_class"
    module = types.ModuleType(module_name)

    class _Source:
        supports_reconnect = False
        is_live = False

        def read(self):
            return False, None

        def release(self):
            return None

        def fps(self):
            return 0.0

    module.CustomSource = _Source
    monkeypatch.setitem(sys.modules, module_name, module)

    source = load_frame_source(f"{module_name}:CustomSource")
    assert source.is_live is False
    assert source.fps() == 0.0
    source.release()


def test_load_frame_source_rejects_non_source(monkeypatch):
    module_name = "tests.fake_source_module_bad"
    module = types.ModuleType(module_name)

    class _Bad:
        pass

    module.BadSource = _Bad
    monkeypatch.setitem(sys.modules, module_name, module)

    with pytest.raises(TypeError, match="not a FrameSource"):
        load_frame_source(f"{module_name}:BadSource")
