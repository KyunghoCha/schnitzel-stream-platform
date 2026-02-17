from __future__ import annotations

from pathlib import Path

from schnitzel_stream.ops import console as console_ops


def test_start_selected_services_builds_commands_and_env(tmp_path: Path):
    repo_root = tmp_path / "repo"
    (repo_root / "apps" / "stream-console").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)

    paths = console_ops.resolve_console_paths(repo_root=repo_root, log_dir=console_ops.DEFAULT_LOG_DIR)
    calls: list[dict[str, object]] = []

    def _fake_start(cmd, log_path, pid_path, env):
        pid = 100 + len(calls)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(pid), encoding="utf-8")
        calls.append(
            {
                "cmd": list(cmd),
                "log_path": str(log_path),
                "pid_path": str(pid_path),
                "env": dict(env),
            }
        )
        return pid

    actions = console_ops.start_selected_services(
        repo_root=repo_root,
        paths=paths,
        python_executable="python",
        api_host="127.0.0.1",
        api_port=18700,
        ui_host="127.0.0.1",
        ui_port=5173,
        allow_local_mutations=True,
        token="secret-token",
        api_only=False,
        ui_only=False,
        start_process_fn=_fake_start,
        is_process_running_fn=lambda _pid: False,
    )

    assert len(actions) == 2
    assert {item["service"] for item in actions} == {"api", "ui"}
    assert len(calls) == 2

    api_call = next(item for item in calls if "stream_control_api.py" in " ".join(item["cmd"]))
    ui_call = next(item for item in calls if item["cmd"][0] == "npm")

    assert "--port" in api_call["cmd"]
    assert "18700" in api_call["cmd"]
    assert str((repo_root / "src").resolve()) in str(api_call["env"].get("PYTHONPATH", ""))
    assert api_call["env"]["SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS"] == "true"
    assert api_call["env"]["SS_CONTROL_API_TOKEN"] == "secret-token"

    assert ui_call["cmd"][:2] == ["npm", "--prefix"]
    assert "run" in ui_call["cmd"]
    assert "dev" in ui_call["cmd"]

    state = console_ops.load_state(paths)
    assert state["token_configured"] is True
    assert state["allow_local_mutations"] is True


def test_start_selected_services_idempotent_when_pid_running(tmp_path: Path):
    repo_root = tmp_path / "repo"
    paths = console_ops.resolve_console_paths(repo_root=repo_root, log_dir=console_ops.DEFAULT_LOG_DIR)
    paths.pid_dir.mkdir(parents=True, exist_ok=True)
    paths.api_pid.write_text("1234", encoding="utf-8")

    called = {"count": 0}

    def _never_start(*_args, **_kwargs):
        called["count"] += 1
        return 9999

    actions = console_ops.start_selected_services(
        repo_root=repo_root,
        paths=paths,
        python_executable="python",
        api_host="127.0.0.1",
        api_port=18700,
        ui_host="127.0.0.1",
        ui_port=5173,
        allow_local_mutations=False,
        token="",
        api_only=True,
        ui_only=False,
        start_process_fn=_never_start,
        is_process_running_fn=lambda pid: pid == 1234,
    )

    assert called["count"] == 0
    assert len(actions) == 1
    assert actions[0]["action"] == "already_running"
    assert actions[0]["pid"] == 1234


def test_collect_status_uses_state_and_health_callback(tmp_path: Path):
    repo_root = tmp_path / "repo"
    paths = console_ops.resolve_console_paths(repo_root=repo_root, log_dir=console_ops.DEFAULT_LOG_DIR)
    paths.pid_dir.mkdir(parents=True, exist_ok=True)
    paths.api_pid.write_text("11", encoding="utf-8")
    paths.ui_pid.write_text("22", encoding="utf-8")
    console_ops.save_state(
        paths,
        console_ops.default_state(
            paths=paths,
            api_host="127.0.0.1",
            api_port=18700,
            ui_host="127.0.0.1",
            ui_port=5173,
            api_enabled=True,
            ui_enabled=True,
        ),
    )

    payload = console_ops.collect_status(
        paths=paths,
        is_process_running_fn=lambda _pid: True,
        health_check_fn=lambda **_kwargs: {
            "ok": False,
            "reachable": True,
            "status_code": 401,
            "reason": "http_error_401",
            "data": {},
        },
        is_port_open_fn=lambda _host, _port: True,
    )

    assert payload["schema_version"] == 1
    assert payload["ready"] is True
    assert payload["api"]["status"] == "running"
    assert payload["api"]["health"]["status_code"] == 401
    assert payload["ui"]["status"] == "running"


def test_stop_all_services_is_idempotent_when_pid_files_missing(tmp_path: Path):
    repo_root = tmp_path / "repo"
    paths = console_ops.resolve_console_paths(repo_root=repo_root, log_dir=console_ops.DEFAULT_LOG_DIR)

    actions = console_ops.stop_all_services(paths=paths, stop_process_fn=lambda _path: (False, None))
    assert len(actions) == 2
    assert all(item["action"] == "not_found" for item in actions)
