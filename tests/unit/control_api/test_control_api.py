from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from schnitzel_stream.control_api import create_app
from schnitzel_stream.control_api import app as app_mod


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_health_contract_local_mode(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert payload["data"]["service"] == "stream_control_api"


def test_token_mode_requires_bearer(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_TOKEN", "abc123")
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    no_auth = client.get("/api/v1/health")
    assert no_auth.status_code == 401

    with_auth = client.get("/api/v1/health", headers={"Authorization": "Bearer abc123"})
    assert with_auth.status_code == 200
    assert with_auth.json()["data"]["token_required"] is True


def test_preset_run_writes_audit(monkeypatch, tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    monkeypatch.setattr(app_mod.preset_ops, "run_subprocess", lambda **_kwargs: 0)
    run_resp = client.post(
        "/api/v1/presets/inproc_demo/run",
        json={"experimental": False, "max_events": 5},
    )
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["status"] == "ok"
    assert body["data"]["returncode"] == 0

    audit_resp = client.get("/api/v1/governance/audit?limit=10")
    assert audit_resp.status_code == 200
    events = audit_resp.json()["data"]["events"]
    assert any(event.get("action") == "preset.run" for event in events)


def test_fleet_stop_contract_and_audit(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.post("/api/v1/fleet/stop", json={"log_dir": str(tmp_path / "no_pid")})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["schema_version"] == 1
    assert payload["data"]["stopped_count"] == 0

    audit_resp = client.get("/api/v1/governance/audit?limit=10")
    events = audit_resp.json()["data"]["events"]
    assert any(event.get("action") == "fleet.stop" for event in events)


def test_policy_snapshot_endpoint(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.get("/api/v1/governance/policy-snapshot")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "allowed_plugin_prefixes" in data
    assert "security_mode" in data


def test_env_check_endpoint_contract(monkeypatch, tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    monkeypatch.setattr(
        app_mod.env_ops,
        "run_checks",
        lambda **_kwargs: [app_mod.env_ops.CheckResult(name="python", required=True, ok=True, detail="ok")],
    )

    resp = client.post("/api/v1/env/check", json={"profile": "base", "strict": True})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["schema_version"] == 1
    assert payload["status"] == "ok"
    assert payload["data"]["exit_code"] == 0


def test_cors_preflight_allows_local_vite_origin(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
