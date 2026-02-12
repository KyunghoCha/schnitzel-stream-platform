from __future__ import annotations

import pytest

from ai.vision.adapters.custom_adapter import CustomModelAdapter


def test_custom_adapter_template_fails_fast_until_implemented():
    with pytest.raises(RuntimeError, match="template"):
        CustomModelAdapter()
