from __future__ import annotations

from pathlib import Path

from ai.pipeline import config as cfg


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_configs_applies_only_selected_dev_profile(monkeypatch, tmp_path: Path):
    configs = tmp_path / "configs"
    _write(
        configs / "default.yaml",
        """
app:
  site_id: "S001"
  env: "dev"
ingest:
  fps_limit: 10
events:
  post_url: "http://x"
heartbeat:
  enabled: true
""".strip(),
    )
    _write(configs / "cameras.yaml", "cameras: []")
    _write(configs / "dev.yaml", "logging:\n  level: \"DEBUG\"\n")
    _write(configs / "prod.yaml", "heartbeat:\n  enabled: false\n")

    monkeypatch.setattr(cfg, "resolve_project_root", lambda: tmp_path)
    monkeypatch.setattr(cfg, "apply_env_overrides", lambda x: x)

    out = cfg._load_configs()
    assert out["logging"]["level"] == "DEBUG"
    # prod profile key must not leak when app.env=dev
    assert out["heartbeat"]["enabled"] is True


def test_load_configs_applies_only_selected_prod_profile(monkeypatch, tmp_path: Path):
    configs = tmp_path / "configs"
    _write(
        configs / "default.yaml",
        """
app:
  site_id: "S001"
  env: "prod"
ingest:
  fps_limit: 10
events:
  post_url: "http://x"
logging:
  level: "DEBUG"
zones:
  source: "api"
""".strip(),
    )
    _write(configs / "cameras.yaml", "cameras: []")
    _write(configs / "dev.yaml", "zones:\n  source: \"file\"\n")
    _write(configs / "prod.yaml", "logging:\n  level: \"INFO\"\n")

    monkeypatch.setattr(cfg, "resolve_project_root", lambda: tmp_path)
    monkeypatch.setattr(cfg, "apply_env_overrides", lambda x: x)

    out = cfg._load_configs()
    assert out["logging"]["level"] == "INFO"
    # dev profile key must not leak when app.env=prod
    assert out["zones"]["source"] == "api"
