from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess
from typing import Mapping


@dataclass(frozen=True)
class PresetSpec:
    preset_id: str
    description: str
    graph: Path
    experimental: bool = False
    env_defaults: Mapping[str, str] | None = None


def repo_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parents[1]


def resolve_input_path(raw: str, *, repo_root: Path) -> str:
    p = Path(raw)
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    return str(p)


def build_preset_table(repo_root: Path) -> dict[str, PresetSpec]:
    graphs = repo_root / "configs" / "graphs"
    return {
        "inproc_demo": PresetSpec(
            preset_id="inproc_demo",
            description="Minimal in-proc packet flow demo",
            graph=graphs / "dev_inproc_demo_v2.yaml",
        ),
        "file_frames": PresetSpec(
            preset_id="file_frames",
            description="Video-file source + frame sampler + print sink",
            graph=graphs / "dev_video_file_frames_v2.yaml",
            env_defaults={
                "SS_INPUT_PATH": str((repo_root / "data" / "samples" / "2048246-hd_1920_1080_24fps.mp4").resolve()),
                "SS_INPUT_LOOP": "false",
            },
        ),
        "webcam_frames": PresetSpec(
            preset_id="webcam_frames",
            description="Webcam source + frame sampler + print sink",
            graph=graphs / "dev_webcam_frames_v2.yaml",
            env_defaults={"SS_CAMERA_INDEX": "0"},
        ),
        "file_yolo": PresetSpec(
            preset_id="file_yolo",
            description="Video-file YOLO overlay (loop + low-latency queue policy)",
            graph=graphs / "dev_video_file_yolo_overlay_v2.yaml",
            experimental=True,
            env_defaults={
                "SS_INPUT_PATH": str((repo_root / "data" / "samples" / "2048246-hd_1920_1080_24fps.mp4").resolve()),
                "SS_YOLO_MODEL_PATH": str((repo_root / "models" / "yolov8n.pt").resolve()),
                "SS_YOLO_DEVICE": "cpu",
                "SS_INPUT_LOOP": "true",
            },
        ),
        "webcam_yolo": PresetSpec(
            preset_id="webcam_yolo",
            description="Webcam YOLO overlay",
            graph=graphs / "dev_webcam_yolo_overlay_v2.yaml",
            experimental=True,
            env_defaults={
                "SS_CAMERA_INDEX": "0",
                "SS_YOLO_MODEL_PATH": str((repo_root / "models" / "yolov8n.pt").resolve()),
                "SS_YOLO_DEVICE": "cpu",
            },
        ),
    }


def list_presets_rows(*, table: Mapping[str, PresetSpec], include_experimental: bool) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for preset_id in sorted(table):
        spec = table[preset_id]
        if spec.experimental and not include_experimental:
            continue
        mark = "yes" if spec.experimental else "no"
        rows.append((spec.preset_id, mark, str(spec.graph), spec.description))
    return rows


def build_preset_env(
    *,
    repo_root: Path,
    spec: PresetSpec,
    existing_env: Mapping[str, str] | None = None,
    input_path: str = "",
    camera_index: int | None = None,
    device: str = "",
    loop: str = "",
) -> dict[str, str]:
    env = dict(existing_env or os.environ)
    py_path = str((repo_root / "src").resolve())
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{existing}" if existing else py_path

    for key, value in (spec.env_defaults or {}).items():
        env.setdefault(str(key), str(value))

    if input_path:
        env["SS_INPUT_PATH"] = resolve_input_path(str(input_path), repo_root=repo_root)
    if camera_index is not None:
        env["SS_CAMERA_INDEX"] = str(int(camera_index))
    if device:
        env["SS_YOLO_DEVICE"] = str(device)
    if loop:
        env["SS_INPUT_LOOP"] = str(loop)

    return env


def shell_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def run_subprocess(*, cmd: list[str], cwd: Path, env: Mapping[str, str]) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd), env=dict(env))
    return int(proc.returncode)
