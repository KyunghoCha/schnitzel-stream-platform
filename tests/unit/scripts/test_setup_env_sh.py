from __future__ import annotations

from pathlib import Path


def _setup_script_text() -> str:
    root = Path(__file__).resolve().parents[3]
    return (root / "setup_env.sh").read_text(encoding="utf-8")


def test_setup_env_sh_supports_standard_flags() -> None:
    text = _setup_script_text()
    assert "--profile" in text
    assert "--manager" in text
    assert "--dry-run" in text
    assert "--skip-doctor" in text


def test_setup_env_sh_keeps_one_cycle_positional_compatibility_notice() -> None:
    text = _setup_script_text().lower()
    assert "positional" in text
    assert "deprecated" in text
