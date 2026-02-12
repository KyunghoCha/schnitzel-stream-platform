from __future__ import annotations

import sys
import types

from ai.pipeline.model_adapter import load_model_adapter


def test_load_model_adapter_composite() -> None:
    module_name = "tests._fake_adapters"
    mod = types.ModuleType(module_name)

    class AdapterA:
        def infer(self, frame):
            return [{"name": "a"}]

    class AdapterB:
        def infer(self, frame):
            return [{"name": "b"}]

    mod.AdapterA = AdapterA
    mod.AdapterB = AdapterB
    sys.modules[module_name] = mod
    try:
        adapter = load_model_adapter(f"{module_name}:AdapterA,{module_name}:AdapterB")
        out = adapter.infer(None)
        assert {"name": "a"} in out
        assert {"name": "b"} in out
        assert len(out) == 2
    finally:
        sys.modules.pop(module_name, None)
