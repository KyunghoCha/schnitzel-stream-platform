# Docs: docs/implementation/70-config/README.md
from __future__ import annotations

# 파이프라인 설정 로더
# - configs/*.yaml 병합
# - 카메라/소스/이벤트 설정 구성

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.config import apply_env_overrides, load_config, validate_config, _deep_merge


@dataclass(frozen=True)
class SourceSettings:
    # 소스 설정
    type: str  # file | rtsp | webcam | plugin
    url: str | None = None
    path: str | None = None
    index: int | None = None
    adapter: str | None = None  # AI_SOURCE_ADAPTER (module:ClassName)


@dataclass(frozen=True)
class SensorSettings:
    # 센서 설정 (P1: 센서 패킷 수집 + 이벤트 주입)
    enabled: bool = False
    type: str | None = None  # ros2 | mqtt | modbus | serial | plugin
    adapter: str | None = None  # 대표 adapter (하위호환)
    adapters: tuple[str, ...] = ()  # AI_SENSOR_ADAPTERS / sensor.adapters
    topic: str | None = None
    queue_size: int = 256
    time_window_ms: int = 300
    emit_events: bool = False
    emit_fused_events: bool = False


@dataclass(frozen=True)
class IngestSettings:
    # 입력(ingest) 설정
    fps_limit: int


@dataclass(frozen=True)
class EventsSettings:
    # 이벤트 전송 설정
    post_url: str
    timeout_sec: float
    retry_max_attempts: int
    retry_backoff_sec: float
    snapshot_base_dir: str | None = None
    snapshot_public_prefix: str | None = None
    emitter_adapter: str | None = None  # AI_EVENTS_EMITTER_ADAPTER (module:ClassName)


@dataclass(frozen=True)
class DedupSettings:
    # 중복 억제 설정
    enabled: bool
    cooldown_sec: float
    prune_interval: int


@dataclass(frozen=True)
class LoggingSettings:
    # 로깅 설정
    level: str
    format: str
    max_bytes: int = 10_485_760  # 10MB
    backup_count: int = 5


@dataclass(frozen=True)
class RtspSettings:
    # RTSP 안정화 설정
    timeout_sec: float
    base_delay_sec: float
    max_delay_sec: float
    max_attempts: int
    jitter_ratio: float
    transport: str  # tcp | udp


@dataclass(frozen=True)
class MetricsSettings:
    # 메트릭 설정
    enabled: bool
    interval_sec: float
    fps_window_sec: float


@dataclass(frozen=True)
class HeartbeatSettings:
    # 하트비트 설정
    enabled: bool
    interval_sec: float


@dataclass(frozen=True)
class RulesSettings:
    # 룰 설정
    rule_point_by_event_type: dict[str, str]


@dataclass(frozen=True)
class ZonesApiSettings:
    # Zones API 설정
    base_url: str
    get_path_template: str
    timeout_sec: float
    cache_ttl_sec: float
    error_backoff_sec: float
    max_failures: int


@dataclass(frozen=True)
class ZonesSettings:
    # Zones 설정
    source: str  # api | file
    file_path: str | None
    api: ZonesApiSettings | None


@dataclass(frozen=True)
class ModelSettings:
    # 모델 설정
    mode: str  # real | mock
    adapter: str | None = None  # AI_MODEL_ADAPTER (module:ClassName)


@dataclass(frozen=True)
class PipelineSettings:
    # 파이프라인 전체 설정
    site_id: str
    timezone: str | None
    camera_id: str
    source: SourceSettings
    sensor: SensorSettings
    ingest: IngestSettings
    events: EventsSettings
    dedup: DedupSettings
    logging: LoggingSettings
    rtsp: RtspSettings
    metrics: MetricsSettings
    heartbeat: HeartbeatSettings
    rules: RulesSettings
    zones: ZonesSettings
    model: ModelSettings


def resolve_project_root() -> Path:
    # repo 루트 계산 (src/ai/pipeline/config.py → 3단계 상위)
    return Path(__file__).resolve().parents[3]


def _resolve_repo_relative_path(path_value: str | None, root: Path) -> str | None:
    """설정 파일의 상대경로를 repo root 기준 절대경로로 정규화한다."""
    if not path_value:
        return None
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return str(path)
    return str((root / path).resolve())


def _first_enabled_camera(cameras: list[dict[str, Any]]) -> dict[str, Any] | None:
    # enabled 카메라 우선 선택
    for cam in cameras:
        if cam.get("enabled", True):
            return cam
    return cameras[0] if cameras else None


def _first_enabled_camera_by_type(cameras: list[dict[str, Any]], source_type: str) -> dict[str, Any] | None:
    # 소스 타입이 맞는 enabled 카메라 선택
    for cam in cameras:
        if not cam.get("enabled", True):
            continue
        source = cam.get("source", {})
        if source.get("type") == source_type:
            return cam
    return None


def _select_camera(
    cameras: list[dict[str, Any]],
    camera_id: str | None,
    prefer_source_type: str | None = None,
) -> dict[str, Any] | None:
    # camera_id 지정이 있으면 우선, 없으면 소스 타입/enable 기준 선택
    if camera_id:
        for cam in cameras:
            cam_id = cam.get("id") or cam.get("camera_id")
            if cam_id == camera_id:
                return cam
        raise ValueError(f"camera_id not found: {camera_id}")
    if prefer_source_type:
        preferred = _first_enabled_camera_by_type(cameras, prefer_source_type)
        if preferred is not None:
            return preferred
    return _first_enabled_camera(cameras)


def _load_configs() -> dict[str, Any]:
    # configs 폴더 로드 (없으면 빈 설정)
    root = resolve_project_root()
    cfg: dict[str, Any] = {}
    configs_dir = root / "configs"

    # 기본 병합 순서 고정:
    # 1) default.yaml
    # 2) cameras.yaml
    # dev/prod는 profile 단계에서만 명시적으로 병합한다.
    for name in ("default.yaml", "cameras.yaml"):
        path = configs_dir / name
        if path.exists():
            cfg = _deep_merge(cfg, load_config(path))

    # 하위 호환: default/cameras가 둘 다 없으면 top-level yaml을 profile 제외 후 병합
    if not cfg and configs_dir.exists():
        for path in sorted(configs_dir.glob("*.yaml")):
            if path.name in ("dev.yaml", "prod.yaml"):
                continue
            cfg = _deep_merge(cfg, load_config(path))

    # 런타임 프로필(dev/prod) 오버라이드
    app_env = cfg.get("app", {}).get("env")
    if app_env in ("dev", "prod"):
        profile_path = root / "configs" / f"{app_env}.yaml"
        if profile_path.exists():
            profile_cfg = load_config(profile_path)
            cfg = _deep_merge(cfg, profile_cfg)
    # 환경변수 오버라이드 (최우선 적용 - 프로필 병합 이후)
    cfg = apply_env_overrides(cfg)
    # 스키마 검증
    validate_config(cfg)
    return cfg


def _parse_adapter_list(raw: Any) -> tuple[str, ...]:
    """sensor.adapters 값을 공백/빈 문자열 제거 후 tuple로 정규화한다."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    if isinstance(raw, (list, tuple)):
        out: list[str] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if text:
                out.append(text)
        return tuple(out)
    return ()


def _merge_single_and_multi_adapter(single: Any, multi: Any) -> tuple[str, ...]:
    """sensor.adapter + sensor.adapters를 우선순위 보존하며 병합한다."""
    out: list[str] = []
    single_text = str(single).strip() if isinstance(single, str) else ""
    if single_text:
        out.append(single_text)
    for path in _parse_adapter_list(multi):
        if path not in out:
            out.append(path)
    return tuple(out)


def load_pipeline_settings(
    camera_id: str | None = None,
    video_override: str | None = None,
    source_type_override: str | None = None,
) -> PipelineSettings:
    # 파이프라인 설정 구성
    cfg = _load_configs()
    root = resolve_project_root()

    app_cfg = cfg.get("app", {})
    site_id = app_cfg.get("site_id", "S000")
    timezone = app_cfg.get("timezone", None)

    cameras = cfg.get("cameras", [])
    # 의도: 명시 옵션이 없을 때는 네트워크 의존성이 없는 file 소스를 우선 선택한다.
    # 로컬 개발/테스트 재현성을 높이고 RTSP 환경 편차 영향을 줄이기 위한 정책.
    # source_type_override가 있으면 해당 타입을 우선한다.
    prefer_file = source_type_override is None
    prefer_type = source_type_override or ("file" if prefer_file else None)
    cam_cfg = _select_camera(cameras, camera_id, prefer_type) or {}

    raw_source_cfg = cam_cfg.get("source", {}) if isinstance(cam_cfg, dict) else {}
    source_cfg = raw_source_cfg if isinstance(raw_source_cfg, dict) else {}
    raw_global_source = cfg.get("source", {})
    global_source_cfg = raw_global_source if isinstance(raw_global_source, dict) else {}
    source_type = source_type_override or (
        "file" if video_override is not None else global_source_cfg.get("type", source_cfg.get("type", "file"))
    )
    source_adapter = global_source_cfg.get("adapter") or source_cfg.get("adapter")
    if source_type in ("rtsp", "plugin"):
        source_path = None
    elif video_override is not None:
        source_path = video_override
    else:
        source_path = _resolve_repo_relative_path(source_cfg.get("path"), root)
    source_url = source_cfg.get("url") if source_type == "rtsp" else None
    source_index: int | None = None
    if source_type == "webcam":
        # 하위 호환: 과거 cameras.yaml에서 webcam index를 path 문자열("0")으로 쓰던 케이스 허용
        raw_index = source_cfg.get("index", source_cfg.get("path"))
        if raw_index is not None:
            try:
                source_index = int(raw_index)
            except (TypeError, ValueError):
                source_index = None

    ingest_cfg = cfg.get("ingest", {})
    ingest = IngestSettings(
        fps_limit=int(ingest_cfg.get("fps_limit", 10)),
    )

    events_cfg = cfg.get("events", {})
    retry_cfg = events_cfg.get("retry", {})
    snapshot_cfg = events_cfg.get("snapshot", {})
    events = EventsSettings(
        post_url=events_cfg.get("post_url", "http://localhost:8080/api/events"),
        timeout_sec=float(events_cfg.get("timeout_sec", 3)),
        retry_max_attempts=int(retry_cfg.get("max_attempts", 5)),
        retry_backoff_sec=float(retry_cfg.get("backoff_sec", 1.0)),
        snapshot_base_dir=snapshot_cfg.get("base_dir"),
        snapshot_public_prefix=snapshot_cfg.get("public_prefix"),
        emitter_adapter=events_cfg.get("emitter_adapter") or None,
    )

    dedup_cfg = cfg.get("dedup", {})
    dedup = DedupSettings(
        enabled=bool(dedup_cfg.get("enabled", False)),
        cooldown_sec=float(dedup_cfg.get("cooldown_sec", 10.0)),
        prune_interval=int(dedup_cfg.get("prune_interval", 100)),
    )

    logging_cfg = cfg.get("logging", {})
    logging_settings = LoggingSettings(
        level=str(logging_cfg.get("level", "INFO")),
        format=str(logging_cfg.get("format", "plain")),
        max_bytes=int(logging_cfg.get("max_bytes", 10_485_760)),
        backup_count=int(logging_cfg.get("backup_count", 5)),
    )

    rtsp_cfg = cfg.get("rtsp", {})
    rtsp = RtspSettings(
        timeout_sec=float(rtsp_cfg.get("timeout_sec", 5.0)),
        base_delay_sec=float(rtsp_cfg.get("base_delay_sec", 0.5)),
        max_delay_sec=float(rtsp_cfg.get("max_delay_sec", 10.0)),
        max_attempts=int(rtsp_cfg.get("max_attempts", 0)),
        jitter_ratio=float(rtsp_cfg.get("jitter_ratio", 0.2)),
        transport=str(rtsp_cfg.get("transport", "tcp")),
    )

    metrics_cfg = cfg.get("metrics", {})
    metrics = MetricsSettings(
        enabled=bool(metrics_cfg.get("enabled", True)),
        interval_sec=float(metrics_cfg.get("interval_sec", 10.0)),
        fps_window_sec=float(metrics_cfg.get("fps_window_sec", 5.0)),
    )

    heartbeat_cfg = cfg.get("heartbeat", {})
    heartbeat = HeartbeatSettings(
        enabled=bool(heartbeat_cfg.get("enabled", True)),
        interval_sec=float(heartbeat_cfg.get("interval_sec", 15.0)),
    )

    rules_cfg = cfg.get("rules", {})
    rules = RulesSettings(
        rule_point_by_event_type=dict(rules_cfg.get("rule_point_by_event_type", {})),
    )

    zones_cfg = cfg.get("zones", {})
    zones_api_cfg = zones_cfg.get("api", {})
    zones_api = None
    if isinstance(zones_api_cfg, dict) and zones_api_cfg:
        zones_api = ZonesApiSettings(
            base_url=str(zones_api_cfg.get("base_url", "")),
            get_path_template=str(zones_api_cfg.get("get_path_template", "")),
            timeout_sec=float(zones_api_cfg.get("timeout_sec", 3.0)),
            cache_ttl_sec=float(zones_api_cfg.get("cache_ttl_sec", 30.0)),
            error_backoff_sec=float(zones_api_cfg.get("error_backoff_sec", 5.0)),
            max_failures=int(zones_api_cfg.get("max_failures", 3)),
        )
    zones = ZonesSettings(
        source=str(zones_cfg.get("source", "api")),
        file_path=_resolve_repo_relative_path(zones_cfg.get("file_path"), root),
        api=zones_api,
    )

    model_cfg = cfg.get("model", {})
    model = ModelSettings(
        mode=str(model_cfg.get("mode", "real")),
        adapter=model_cfg.get("adapter") or None,
    )

    source = SourceSettings(
        type=source_type,
        url=source_url,
        path=source_path,
        index=source_index,
        adapter=source_adapter or None,
    )
    sensor_cfg_raw = cfg.get("sensor", {})
    sensor_cfg = sensor_cfg_raw if isinstance(sensor_cfg_raw, dict) else {}
    sensor_adapters = _merge_single_and_multi_adapter(
        sensor_cfg.get("adapter"),
        sensor_cfg.get("adapters"),
    )
    sensor = SensorSettings(
        enabled=bool(sensor_cfg.get("enabled", False)),
        type=sensor_cfg.get("type") or None,
        adapter=sensor_adapters[0] if sensor_adapters else None,
        adapters=sensor_adapters,
        topic=sensor_cfg.get("topic") or None,
        queue_size=int(sensor_cfg.get("queue_size", 256)),
        time_window_ms=int(sensor_cfg.get("time_window_ms", 300)),
        emit_events=bool(sensor_cfg.get("emit_events", False)),
        emit_fused_events=bool(sensor_cfg.get("emit_fused_events", False)),
    )

    resolved_camera_id = cam_cfg.get("id") or cam_cfg.get("camera_id") or camera_id or "cam00"
    return PipelineSettings(
        site_id=site_id,
        timezone=timezone,
        camera_id=resolved_camera_id,
        source=source,
        sensor=sensor,
        ingest=ingest,
        events=events,
        dedup=dedup,
        logging=logging_settings,
        rtsp=rtsp,
        metrics=metrics,
        heartbeat=heartbeat,
        rules=rules,
        zones=zones,
        model=model,
    )
