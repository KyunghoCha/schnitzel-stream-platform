from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_stream_run_module() -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    mod_path = root / "scripts" / "stream_run.py"
    spec = importlib.util.spec_from_file_location("stream_run_test_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_list_hides_experimental_by_default(capsys):
    mod = _load_stream_run_module()
    code = mod.run(["--list"])
    assert code == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "inproc_demo" in out
    assert "file_frames" in out
    assert "webcam_frames" in out
    assert "file_yolo" not in out
    assert "webcam_yolo" not in out


def test_list_shows_experimental_with_flag(capsys):
    mod = _load_stream_run_module()
    code = mod.run(["--list", "--experimental"])
    assert code == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "file_yolo" in out
    assert "webcam_yolo" in out


def test_experimental_preset_requires_opt_in(capsys):
    mod = _load_stream_run_module()
    code = mod.run(["--preset", "file_yolo", "--validate-only"])
    assert code == mod.EXIT_USAGE
    err = capsys.readouterr().err
    assert "experimental" in err.lower()


def test_unknown_preset_returns_usage(capsys):
    mod = _load_stream_run_module()
    code = mod.run(["--preset", "does_not_exist"])
    assert code == mod.EXIT_USAGE
    err = capsys.readouterr().err
    assert "unknown preset" in err.lower()


def test_run_validate_only_uses_expected_command_and_env(monkeypatch, capsys):
    mod = _load_stream_run_module()
    observed: dict[str, object] = {}

    def _fake_run(*, cmd, cwd, env):
        observed["cmd"] = list(cmd)
        observed["cwd"] = str(cwd)
        observed["env"] = dict(env)
        return 0

    monkeypatch.setattr(mod, "_run_subprocess", _fake_run)

    code = mod.run(
        [
            "--preset",
            "file_yolo",
            "--experimental",
            "--validate-only",
            "--input-path",
            "data/samples/2048246-hd_1920_1080_24fps.mp4",
            "--device",
            "0",
            "--loop",
            "false",
            "--camera-index",
            "3",
            "--max-events",
            "30",
        ]
    )
    assert code == mod.EXIT_OK

    cmd = observed["cmd"]
    assert cmd[0].endswith("python") or "python" in cmd[0].lower()
    assert cmd[1:4] == ["-m", "schnitzel_stream", "validate"]
    assert "--graph" in cmd
    assert "--max-events" in cmd
    assert "30" in cmd

    env = observed["env"]
    assert env["SS_INPUT_PATH"].endswith("data/samples/2048246-hd_1920_1080_24fps.mp4")
    assert env["SS_YOLO_DEVICE"] == "0"
    assert env["SS_INPUT_LOOP"] == "false"
    assert env["SS_CAMERA_INDEX"] == "3"
    assert "PYTHONPATH" in env

    out = capsys.readouterr().out
    assert "preset=file_yolo" in out
    assert "validate_only=True" in out


def test_run_returns_run_failed_on_nonzero_subprocess(monkeypatch):
    mod = _load_stream_run_module()
    monkeypatch.setattr(mod, "_run_subprocess", lambda **_kwargs: 9)
    code = mod.run(["--preset", "inproc_demo", "--validate-only"])
    assert code == mod.EXIT_RUN_FAILED


def test_run_rejects_invalid_max_events(capsys):
    mod = _load_stream_run_module()
    code = mod.run(["--preset", "inproc_demo", "--max-events", "0"])
    assert code == mod.EXIT_USAGE
    err = capsys.readouterr().err
    assert "max-events" in err
