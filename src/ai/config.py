# Docs: docs/implementation/70-config/README.md
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union
import os
from omegaconf import OmegaConf

PathLike = Union[str, Path]

def _as_paths(config_paths: Union[PathLike, Iterable[PathLike]]) -> list[Path]:
    # str은 Iterable이라 그대로 돌리면 문자 단위로 쪼개지는 사고가 나서 여기서 분기
    if isinstance(config_paths, (str, Path)):
        return [Path(config_paths)]
    return [Path(p) for p in config_paths]

def _expand_path(p: Path) -> list[Path]:
    """
    - 파일이면 [파일]
    - 디렉터리면 내부의 *.yaml, *.yml 파일들을 이름순 정렬해서 반환
    """
    if p.is_dir():
        files = sorted([*p.glob("*.yaml"), *p.glob("*.yml")], key=lambda x: x.name)
        if not files:
            raise FileNotFoundError(f"No YAML files in directory: {p.resolve()}")
        return files
    return [p]

def load_config(config_paths: Union[PathLike, Iterable[PathLike]]) -> dict:
    roots = _as_paths(config_paths)

    cfg = OmegaConf.create({})
    for root in roots:
        root = Path(root)
        if not root.exists():
            raise FileNotFoundError(f"Config not found: {root.resolve()}")

        for path in _expand_path(root):
            if not path.exists():
                raise FileNotFoundError(f"Config not found: {path.resolve()}")
            if path.suffix not in (".yaml", ".yml"):
                raise ValueError(f"Not a YAML file: {path.resolve()}")

            layer = OmegaConf.load(path)

            # top-level dict 검증
            cont = OmegaConf.to_container(layer, resolve=False)
            if not isinstance(cont, dict):
                raise ValueError(f"Top-level YAML must be a mapping(dict): {path.resolve()}")

            cfg = OmegaConf.merge(cfg, layer)

    return OmegaConf.to_container(cfg, resolve=True)


def _deep_merge(dst: dict, src: dict) -> dict:
    # dict 깊은 병합 (src가 우선)
    out = dict(dst)
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _coerce_env_value(val: str) -> str | int | float | bool:
    """환경변수 문자열을 적절한 파이썬 타입으로 변환한다."""
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        return val


def apply_env_overrides(cfg: dict) -> dict:
    # 환경변수 기반 오버라이드
    # - 예: AI_EVENTS_POST_URL -> events.post_url
    mapping = {
        "AI_EVENTS_POST_URL": ("events", "post_url"),
        "AI_INGEST_FPS_LIMIT": ("ingest", "fps_limit"),
        "AI_EVENTS_SNAPSHOT_BASE_DIR": ("events", "snapshot", "base_dir"),
        "AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX": ("events", "snapshot", "public_prefix"),
        "AI_EVENTS_EMITTER_ADAPTER": ("events", "emitter_adapter"),
        "AI_SOURCE_TYPE": ("source", "type"),
        "AI_SOURCE_ADAPTER": ("source", "adapter"),
        "AI_SENSOR_ENABLED": ("sensor", "enabled"),
        "AI_SENSOR_TYPE": ("sensor", "type"),
        "AI_SENSOR_ADAPTER": ("sensor", "adapter"),
        "AI_SENSOR_ADAPTERS": ("sensor", "adapters"),
        "AI_SENSOR_TOPIC": ("sensor", "topic"),
        "AI_SENSOR_QUEUE_SIZE": ("sensor", "queue_size"),
        "AI_SENSOR_TIME_WINDOW_MS": ("sensor", "time_window_ms"),
        "AI_SENSOR_EMIT_EVENTS": ("sensor", "emit_events"),
        "AI_SENSOR_EMIT_FUSED_EVENTS": ("sensor", "emit_fused_events"),
        "AI_LOGGING_LEVEL": ("logging", "level"),
        "AI_LOGGING_FORMAT": ("logging", "format"),
        "AI_LOG_LEVEL": ("logging", "level"),
        "AI_LOG_FORMAT": ("logging", "format"),
        "AI_LOG_MAX_BYTES": ("logging", "max_bytes"),
        "AI_LOG_BACKUP_COUNT": ("logging", "backup_count"),
        "AI_MODEL_MODE": ("model", "mode"),
        "AI_MODEL_ADAPTER": ("model", "adapter"),
        "AI_ZONES_SOURCE": ("zones", "source"),
        "AI_RTSP_TIMEOUT_SEC": ("rtsp", "timeout_sec"),
        "AI_RTSP_MAX_ATTEMPTS": ("rtsp", "max_attempts"),
        "AI_RTSP_BASE_DELAY_SEC": ("rtsp", "base_delay_sec"),
        "AI_RTSP_MAX_DELAY_SEC": ("rtsp", "max_delay_sec"),
        "AI_RTSP_TRANSPORT": ("rtsp", "transport"),
    }

    overrides = {}
    for env_key, path in mapping.items():
        if env_key not in os.environ:
            continue
        val = _coerce_env_value(os.environ[env_key])

        cur = overrides
        for p in path[:-1]:
            cur = cur.setdefault(p, {})
        cur[path[-1]] = val

    if overrides:
        return _deep_merge(cfg, overrides)
    return cfg


def validate_config(cfg: dict) -> None:
    # 필수 키/타입 검증
    required = ["app", "ingest", "events"]
    for key in required:
        if key not in cfg:
            raise ValueError(f"Missing required config section: {key}")

    # model.mode가 mock인데 app.env가 prod이면 경고
    import logging
    _logger = logging.getLogger(__name__)
    app_env = cfg.get("app", {}).get("env", "dev")
    model_mode = cfg.get("model", {}).get("mode", "real")
    if model_mode not in ("real", "mock"):
        raise ValueError("model.mode must be 'real' or 'mock'")
    if app_env == "prod" and model_mode != "real":
        _logger.warning(
            "model.mode='%s' in production environment -- "
            "pipeline will emit fake events. "
            "Set model.mode='real' and configure AI_MODEL_ADAPTER for production use.",
            model_mode,
        )
    model_cfg = cfg.get("model", {})
    adapter = model_cfg.get("adapter")
    if adapter is not None and not isinstance(adapter, str):
        raise ValueError("model.adapter must be str")

    ingest = cfg.get("ingest", {})
    if "fps_limit" in ingest and not isinstance(ingest["fps_limit"], (int, float)):
        raise ValueError("ingest.fps_limit must be number")

    events = cfg.get("events", {})
    if "post_url" in events and not isinstance(events["post_url"], str):
        raise ValueError("events.post_url must be str")
    emitter_adapter = events.get("emitter_adapter")
    if emitter_adapter is not None and not isinstance(emitter_adapter, str):
        raise ValueError("events.emitter_adapter must be str")

    snapshot = events.get("snapshot", {})
    if snapshot and snapshot.get("base_dir") is None:
        raise ValueError("events.snapshot.base_dir required when snapshot is configured")

    cameras = cfg.get("cameras", [])
    if cameras is not None and not isinstance(cameras, list):
        raise ValueError("cameras must be list")

    global_source = cfg.get("source", {})
    if global_source and not isinstance(global_source, dict):
        raise ValueError("source must be mapping")
    if isinstance(global_source, dict):
        g_type = global_source.get("type")
        if g_type is not None and not isinstance(g_type, str):
            raise ValueError("source.type must be str")
        if isinstance(g_type, str) and g_type not in ("file", "rtsp", "webcam", "plugin"):
            raise ValueError(f"unsupported source.type: {g_type}")
        g_adapter = global_source.get("adapter")
        if g_adapter is not None and not isinstance(g_adapter, str):
            raise ValueError("source.adapter must be str")

    zones_cfg = cfg.get("zones", {})
    if zones_cfg and not isinstance(zones_cfg, dict):
        raise ValueError("zones must be mapping")
    if isinstance(zones_cfg, dict):
        zones_source = zones_cfg.get("source")
        if zones_source is not None and not isinstance(zones_source, str):
            raise ValueError("zones.source must be str")
        if isinstance(zones_source, str) and zones_source not in ("api", "file", "none"):
            raise ValueError("zones.source must be one of: api, file, none")

    sensor_cfg = cfg.get("sensor", {})
    if sensor_cfg and not isinstance(sensor_cfg, dict):
        raise ValueError("sensor must be mapping")
    if isinstance(sensor_cfg, dict):
        enabled = sensor_cfg.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("sensor.enabled must be bool")
        s_type = sensor_cfg.get("type")
        if s_type is not None and not isinstance(s_type, str):
            raise ValueError("sensor.type must be str")
        s_adapter = sensor_cfg.get("adapter")
        if s_adapter is not None and not isinstance(s_adapter, str):
            raise ValueError("sensor.adapter must be str")
        s_adapters = sensor_cfg.get("adapters")
        if s_adapters is not None:
            if isinstance(s_adapters, str):
                pass
            elif isinstance(s_adapters, list):
                for item in s_adapters:
                    if not isinstance(item, str):
                        raise ValueError("sensor.adapters items must be str")
                    if not item.strip():
                        raise ValueError("sensor.adapters items must be non-empty str")
            else:
                raise ValueError("sensor.adapters must be list[str] or comma-separated str")
        s_topic = sensor_cfg.get("topic")
        if s_topic is not None and not isinstance(s_topic, str):
            raise ValueError("sensor.topic must be str")
        s_queue_size = sensor_cfg.get("queue_size")
        if s_queue_size is not None and (not isinstance(s_queue_size, int) or s_queue_size <= 0):
            raise ValueError("sensor.queue_size must be positive int")
        s_time_window = sensor_cfg.get("time_window_ms")
        if s_time_window is not None and (not isinstance(s_time_window, int) or s_time_window <= 0):
            raise ValueError("sensor.time_window_ms must be positive int")
        s_emit_events = sensor_cfg.get("emit_events")
        if s_emit_events is not None and not isinstance(s_emit_events, bool):
            raise ValueError("sensor.emit_events must be bool")
        s_emit_fused_events = sensor_cfg.get("emit_fused_events")
        if s_emit_fused_events is not None and not isinstance(s_emit_fused_events, bool):
            raise ValueError("sensor.emit_fused_events must be bool")

        # 의도: 센서 경로를 명시적으로 설정할 때 adapter 누락을 즉시 실패시킨다.
        has_single = isinstance(s_adapter, str) and bool(s_adapter.strip())
        has_multi = False
        if isinstance(s_adapters, str):
            has_multi = any(part.strip() for part in s_adapters.split(","))
        elif isinstance(s_adapters, list):
            has_multi = any(isinstance(item, str) and item.strip() for item in s_adapters)
        if enabled is True and not (has_single or has_multi):
            raise ValueError(
                "enabled sensor requires sensor.adapter or sensor.adapters "
                "(AI_SENSOR_ADAPTER / AI_SENSOR_ADAPTERS)",
            )

    seen_camera_ids: set[str] = set()
    for cam in cameras or []:
        if not isinstance(cam, dict):
            raise ValueError("camera item must be mapping")
        cam_id = cam.get("id") or cam.get("camera_id")
        if cam_id:
            cam_id_str = str(cam_id)
            if cam_id_str in seen_camera_ids:
                raise ValueError(f"duplicate camera id: {cam_id_str}")
            seen_camera_ids.add(cam_id_str)

        source = cam.get("source", {})
        if not isinstance(source, dict):
            continue
        source_type = source.get("type", "file")
        if not isinstance(source_type, str):
            raise ValueError("camera source.type must be str")
        if source_type not in ("file", "rtsp", "webcam", "plugin"):
            raise ValueError(f"unsupported camera source.type: {source_type}")
        if source_type == "webcam":
            index = source.get("index")
            if index is not None and not isinstance(index, int):
                raise ValueError("webcam source.index must be int")
        if source_type == "plugin":
            adapter = source.get("adapter")
            if not isinstance(adapter, str) or not adapter.strip():
                raise ValueError("plugin source requires source.adapter (module:ClassName)")
