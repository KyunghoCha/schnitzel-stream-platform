from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
import tempfile
from typing import Literal


DEFAULT_LOG_DIR = str(tempfile.gettempdir()) + "/schnitzel_stream_fleet_run"


class PresetRequest(BaseModel):
    experimental: bool = False
    max_events: int | None = None
    input_path: str = ""
    camera_index: int | None = None
    device: str = ""
    model_path: str = ""
    yolo_conf: float | None = None
    yolo_iou: float | None = None
    yolo_max_det: int | None = None
    loop: Literal["", "true", "false"] = ""


class FleetStartRequest(BaseModel):
    config: str = "configs/fleet.yaml"
    graph_template: str = "configs/graphs/dev_stream_template_v2.yaml"
    log_dir: str = DEFAULT_LOG_DIR
    streams: str = ""
    extra_args: str = ""


class FleetStopRequest(BaseModel):
    log_dir: str = DEFAULT_LOG_DIR


class EnvCheckRequest(BaseModel):
    profile: Literal["base", "yolo", "webcam"] = "base"
    strict: bool = False
    model_path: str = "models/yolov8n.pt"
    camera_index: int = 0
    probe_webcam: bool = False


class Envelope(BaseModel):
    schema_version: int = 1
    status: Literal["ok", "error"] = "ok"
    request_id: str
    ts: datetime
    data: dict[str, object] = Field(default_factory=dict)
    error: dict[str, object] | None = None
