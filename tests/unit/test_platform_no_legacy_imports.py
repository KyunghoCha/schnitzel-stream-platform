from __future__ import annotations

import re
from pathlib import Path


def test_platform_code_does_not_import_legacy_ai_directly():
    root = Path(__file__).resolve().parents[2]
    base = root / "src" / "schnitzel_stream"

    # Allowed: the strangler job that intentionally bridges to legacy runtime.
    allowed = {base / "jobs" / "legacy_ai_pipeline.py"}

    pattern = re.compile(r"^\\s*(from\\s+ai\\b|import\\s+ai\\b)", re.MULTILINE)

    offenders: list[str] = []
    for p in base.rglob("*.py"):
        if p in allowed:
            continue
        text = p.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(p.relative_to(root)))

    assert offenders == [], f"legacy imports found in platform code: {offenders}"

