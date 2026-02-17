from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request

from schnitzel_stream.control_api import app as app_mod
from schnitzel_stream.control_api import auth as auth_mod
from schnitzel_stream.control_api import create_app
from schnitzel_stream.ops import graph_editor as editor_ops


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


def test_token_mode_requires_valid_bearer(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_TOKEN", "abc123")
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    no_auth = client.get("/api/v1/health")
    assert no_auth.status_code == 401

    invalid = client.get("/api/v1/health", headers={"Authorization": "Bearer wrong"})
    assert invalid.status_code == 401

    with_auth = client.get("/api/v1/health", headers={"Authorization": "Bearer abc123"})
    assert with_auth.status_code == 200
    assert with_auth.json()["data"]["token_required"] is True


def test_mutating_endpoint_requires_bearer_without_override(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    run_resp = client.post(
        "/api/v1/presets/inproc_demo/run",
        json={"experimental": False, "max_events": 5},
    )
    assert run_resp.status_code == 401
    assert "mutating endpoint" in run_resp.text


def test_mutating_endpoint_allowed_with_local_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS", "true")
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


def test_preset_run_forwards_yolo_override_fields(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS", "true")
    observed: dict[str, object] = {}

    def _fake_run_subprocess(*, cmd, cwd, env):
        observed["cmd"] = list(cmd)
        observed["cwd"] = str(cwd)
        observed["env"] = dict(env)
        return 0

    monkeypatch.setattr(app_mod.preset_ops, "run_subprocess", _fake_run_subprocess)

    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)
    run_resp = client.post(
        "/api/v1/presets/file_yolo_headless/run",
        json={
            "experimental": True,
            "max_events": 5,
            "model_path": "models/yolov8n.pt",
            "device": "cpu",
            "yolo_conf": 0.41,
            "yolo_iou": 0.52,
            "yolo_max_det": 88,
        },
    )
    assert run_resp.status_code == 200

    env = observed["env"]
    assert env["SS_YOLO_MODEL_PATH"].replace("\\", "/").endswith("models/yolov8n.pt")
    assert env["SS_YOLO_DEVICE"] == "cpu"
    assert env["SS_YOLO_CONF"] == "0.41"
    assert env["SS_YOLO_IOU"] == "0.52"
    assert env["SS_YOLO_MAX_DET"] == "88"


def test_fleet_stop_requires_bearer_without_override(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.post("/api/v1/fleet/stop", json={"log_dir": str(tmp_path / "no_pid")})
    assert resp.status_code == 401


def test_fleet_stop_contract_and_audit_with_local_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS", "true")
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
    assert "mutation_auth_mode" in data
    assert "audit_retention" in data


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


def test_remote_host_is_forbidden_in_local_only_mode():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
        "headers": [],
        "client": ("203.0.113.10", 12345),
    }
    req = Request(scope)

    with pytest.raises(HTTPException) as exc:
        auth_mod.request_identity(req, mode="read")

    assert exc.value.status_code == 403


def test_graph_profiles_endpoint_contract(monkeypatch, tmp_path: Path):
    profile = app_mod.wizard_ops.GraphWizardProfile
    table = {
        "inproc_demo": profile(
            profile_id="inproc_demo",
            description="demo",
            template_path=Path("configs/graphs/templates/inproc_demo_v2.template.yaml"),
            experimental=False,
            defaults={},
        )
    }
    monkeypatch.setattr(app_mod.wizard_ops, "load_profile_table", lambda _root: table)
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.get("/api/v1/graph/profiles")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["data"]["count"] == 1
    assert payload["data"]["profiles"][0]["profile_id"] == "inproc_demo"


def test_graph_from_profile_endpoint_returns_spec(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        app_mod.editor_ops,
        "render_profile_spec",
        lambda **_kwargs: editor_ops.GraphProfileRenderResult(
            profile_id="inproc_demo",
            spec={
                "version": 2,
                "nodes": [
                    {
                        "id": "src",
                        "kind": "source",
                        "plugin": "schnitzel_stream.nodes.dev:StaticSource",
                        "config": {"packets": []},
                    },
                    {
                        "id": "out",
                        "kind": "sink",
                        "plugin": "schnitzel_stream.nodes.dev:PrintSink",
                        "config": {},
                    },
                ],
                "edges": [{"src": "src", "dst": "out"}],
                "config": {},
            },
            experimental=False,
            overrides={"MAX_EVENTS": "30"},
            max_events=30,
            template_path=Path("configs/graphs/templates/inproc_demo_v2.template.yaml"),
        ),
    )
    monkeypatch.setattr(
        app_mod.editor_ops,
        "validate_graph_spec",
        lambda _spec: editor_ops.GraphValidationResult(ok=True, error="", node_count=2, edge_count=1),
    )

    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)
    resp = client.post(
        "/api/v1/graph/from-profile",
        json={
            "profile_id": "inproc_demo",
            "experimental": False,
            "overrides": {},
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["data"]["profile_id"] == "inproc_demo"
    assert payload["data"]["validation"]["ok"] is True


def test_graph_validate_endpoint_reports_validation_error(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        app_mod.editor_ops,
        "validate_graph_spec",
        lambda _spec: editor_ops.GraphValidationResult(ok=False, error="broken graph", node_count=0, edge_count=0),
    )
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.post(
        "/api/v1/graph/validate",
        json={"spec": {"version": 2, "nodes": [], "edges": [], "config": {}}},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "error"
    assert payload["error"]["kind"] == "graph_validation_failed"


def test_graph_run_requires_bearer_without_override(tmp_path: Path):
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.post(
        "/api/v1/graph/run",
        json={"spec": {"version": 2, "nodes": [], "edges": [], "config": {}}, "max_events": 5},
    )
    assert resp.status_code == 401


def test_graph_run_allowed_with_local_override_and_audit(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS", "true")
    monkeypatch.setattr(
        app_mod.editor_ops,
        "run_graph_spec",
        lambda **_kwargs: editor_ops.GraphRunResult(
            ok=True,
            returncode=0,
            command="python -m schnitzel_stream --graph outputs/tmp/editor.yaml --max-events 5",
            temp_spec_path=tmp_path / "editor.yaml",
            error="",
            stdout_tail="ok",
            stderr_tail="",
        ),
    )
    app = create_app(repo_root=_repo_root(), audit_path=tmp_path / "audit.jsonl")
    client = TestClient(app)

    resp = client.post(
        "/api/v1/graph/run",
        json={"spec": {"version": 2, "nodes": [], "edges": [], "config": {}}, "max_events": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["data"]["returncode"] == 0

    audit_resp = client.get("/api/v1/governance/audit?limit=20")
    assert audit_resp.status_code == 200
    events = audit_resp.json()["data"]["events"]
    assert any(event.get("action") == "graph.run" for event in events)
