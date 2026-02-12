# Docs: docs/specs/pipeline_spec.md, docs/design/pipeline_design.md
from __future__ import annotations

# 파이프라인 실행 엔트리포인트
# - CLI 파싱
# - 소스/빌더/에미터 구성

import argparse
import logging
import signal
import socket
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from ai.clients.backend_api import BackendClientConfig
from ai.logging_setup import setup_logging, set_log_context
from ai.pipeline.config import load_pipeline_settings, PipelineSettings, RtspSettings, resolve_project_root
from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.emitters import BackendEmitter, FileEmitter, StdoutEmitter, EventEmitter, load_event_emitter
from ai.pipeline.events import MockModelEventBuilder, RealModelEventBuilder
from ai.pipeline.model_adapter import load_model_adapter
from ai.pipeline.sensors import (
    load_sensor_source,
    MultiSensorRuntime,
    SensorRuntime,
    SensorRuntimeLike,
    SensorAwareEventBuilder,
    SensorEventBuilder,
)
from ai.pipeline.sampler import FrameSampler
from ai.pipeline.sources import FileSource, RtspSource, WebcamSource, load_frame_source
from ai.rules.dedup import DedupController
from ai.rules.zones import ZoneEvaluator
from ai.utils.metrics import MetricsTracker, Heartbeat
from ai.utils.urls import mask_url
from ai.vision.visualizer import OpencvVisualizer

logger = logging.getLogger(__name__)


def _resolve_sample_video() -> str:
    # data/samples/*.mp4 중 첫 번째 파일 선택
    sample_dir = resolve_project_root() / "data" / "samples"
    mp4s = sorted(sample_dir.glob("*.mp4"))
    if not mp4s:
        raise FileNotFoundError(f"No mp4 files under: {sample_dir}")
    return str(mp4s[0])


def _parse_args() -> argparse.Namespace:
    # CLI 인자 파싱
    parser = argparse.ArgumentParser(description="File/RTSP -> AI -> backend pipeline")
    parser.add_argument("--camera-id", type=str, default=None, help="camera id override")
    parser.add_argument("--video", type=str, default=None, help="mp4 file path override")
    parser.add_argument(
        "--source-type",
        type=str,
        choices=("file", "rtsp", "webcam", "plugin"),
        default=None,
        help="override source type",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="webcam device index override (default: camera config index or 0)",
    )
    parser.add_argument("--dry-run", action="store_true", help="do not post to backend")
    parser.add_argument("--output-jsonl", type=str, default=None, help="write events to jsonl file")
    parser.add_argument("--max-events", type=int, default=None, help="limit emitted events")
    parser.add_argument("--visualize", action="store_true", help="show debug window with detections")
    parser.add_argument("--loop", action="store_true", help="loop video file indefinitely")
    return parser.parse_args()


def _build_source(
    source_type: str,
    video_override: str | None,
    source_path: str | None,
    source_url: str | None,
    source_adapter: str | None,
    camera_index: int,
    rtsp_cfg: RtspSettings | None,
    loop: bool = False,
):
    # 소스 타입에 따라 FileSource 또는 RtspSource 생성
    if source_type == "plugin":
        adapter_path = (source_adapter or "").strip()
        if not adapter_path:
            raise RuntimeError(
                "plugin source requires source.adapter / AI_SOURCE_ADAPTER (module:ClassName)",
            )
        return load_frame_source(adapter_path)

    if source_type == "webcam":
        return WebcamSource(camera_index)

    if source_type == "rtsp":
        if not source_url:
            raise ValueError("rtsp source requires url")
        return RtspSource(
            source_url,
            timeout_sec=rtsp_cfg.timeout_sec,
            base_delay_sec=rtsp_cfg.base_delay_sec,
            max_delay_sec=rtsp_cfg.max_delay_sec,
            max_attempts=rtsp_cfg.max_attempts,
            jitter_ratio=rtsp_cfg.jitter_ratio,
            transport=rtsp_cfg.transport,
        )

    if video_override is not None:
        if not Path(video_override).exists():
            raise FileNotFoundError(f"video file not found: {video_override}")
        path = video_override
    else:
        path = source_path
        if path and not Path(path).exists():
            # 의도: 로컬 개발/데모 편의성.
            # 설정 파일 경로가 깨진 경우 즉시 중단하지 않고 샘플 영상으로 폴백한다.
            # (반대로 --video 명시 입력은 fail-fast 유지)
            logger.warning("configured source path not found: %s, falling back to sample video", path)
            path = None
        path = path or _resolve_sample_video()
    return FileSource(path, loop=loop)


def _build_event_builder(settings: PipelineSettings, snapshot_base_dir: str | None):
    # model.mode에 따라 이벤트 빌더 생성
    if settings.model.mode == "mock":
        return MockModelEventBuilder(
            settings.site_id,
            settings.camera_id,
            settings.timezone,
            snapshot_base_dir,
            settings.events.snapshot_public_prefix,
        )
    if settings.model.mode == "real":
        adapter_path = (settings.model.adapter or "").strip()
        if not adapter_path:
            raise RuntimeError(
                "model.mode=real requires AI_MODEL_ADAPTER (e.g., ai.vision.adapters.yolo_adapter:YOLOAdapter)"
            )
        adapter = load_model_adapter(adapter_path)
        return RealModelEventBuilder(
            settings.site_id,
            settings.camera_id,
            adapter,
            settings.timezone,
            snapshot_base_dir,
            settings.events.snapshot_public_prefix,
        )
    raise ValueError(f"unsupported model.mode: {settings.model.mode!r} (supported: 'real' | 'mock')")


def _resolve_sensor_adapter_paths(settings: PipelineSettings) -> list[str]:
    paths: list[str] = []
    for path in getattr(settings.sensor, "adapters", ()) or ():
        if not isinstance(path, str):
            continue
        text = path.strip()
        if text and text not in paths:
            paths.append(text)
    single = (settings.sensor.adapter or "").strip()
    if single and single not in paths:
        paths.insert(0, single)
    return paths


def _build_sensor_runtime(
    settings: PipelineSettings,
    metrics: MetricsTracker | None = None,
) -> SensorRuntimeLike | None:
    if not settings.sensor.enabled:
        return None
    adapter_paths = _resolve_sensor_adapter_paths(settings)
    if not adapter_paths:
        raise RuntimeError(
            "sensor.enabled=true requires sensor.adapter or sensor.adapters "
            "(AI_SENSOR_ADAPTER / AI_SENSOR_ADAPTERS)",
        )
    runtimes: list[SensorRuntime] = []
    for adapter_path in adapter_paths:
        source = load_sensor_source(adapter_path)
        runtimes.append(
            SensorRuntime(
                source=source,
                queue_size=settings.sensor.queue_size,
                sensor_type_hint=settings.sensor.type,
                topic_hint=settings.sensor.topic,
                on_packet=metrics.on_sensor_packet if metrics is not None else None,
                on_drop=metrics.on_sensor_drop if metrics is not None else None,
                on_error=metrics.on_sensor_error if metrics is not None else None,
            )
        )
    if len(runtimes) == 1:
        return runtimes[0]
    return MultiSensorRuntime(runtimes)


def _build_emitter(
    settings: PipelineSettings,
    args: argparse.Namespace,
    metrics: MetricsTracker | None = None,
) -> EventEmitter:
    # 에미터 생성 (jsonl > dry-run > backend 순서)
    if args.output_jsonl:
        return FileEmitter(args.output_jsonl)
    if args.dry_run:
        return StdoutEmitter()
    emitter_adapter_path = (getattr(settings.events, "emitter_adapter", None) or "").strip()
    if emitter_adapter_path:
        # 의도: 출력 경로도 모델 어댑터처럼 플러그인 확장 가능하게 유지한다.
        # 단, jsonl/dry-run 명시 실행은 항상 우선한다.
        return load_event_emitter(emitter_adapter_path)

    masked_post_url = mask_url(settings.events.post_url)
    host = urlparse(settings.events.post_url).hostname
    if not host:
        logger.warning("invalid post_url (no host): %s, falling back to dry-run", masked_post_url)
        return StdoutEmitter()
    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        # 의도: 개발/검증 단계에서 백엔드 DNS 미해결이 파이프라인 자체 실행을 막지 않도록
        # 하드 실패 대신 dry-run으로 강등한다.
        logger.warning("backend host not resolvable: %s, falling back to dry-run", host)
        return StdoutEmitter()
    return BackendEmitter(
        BackendClientConfig(
            post_url=settings.events.post_url,
            timeout_sec=settings.events.timeout_sec,
            retry_max_attempts=settings.events.retry_max_attempts,
            retry_backoff_sec=settings.events.retry_backoff_sec,
        ),
        delivery_callback=metrics.on_backend_ack if metrics is not None else None,
    )


def _build_zone_evaluator(settings: PipelineSettings) -> ZoneEvaluator | None:
    # zone evaluator 생성
    # zones.source=none이면 zone 평가를 비활성화한다.
    if settings.zones.source not in ("api", "file"):
        return None
    return ZoneEvaluator(
        source=settings.zones.source,
        site_id=settings.site_id,
        camera_id=settings.camera_id,
        rule_map=settings.rules.rule_point_by_event_type,
        api_cfg={
            "base_url": settings.zones.api.base_url,
            "get_path_template": settings.zones.api.get_path_template,
            "timeout_sec": settings.zones.api.timeout_sec,
            "cache_ttl_sec": settings.zones.api.cache_ttl_sec,
            "error_backoff_sec": settings.zones.api.error_backoff_sec,
            "max_failures": settings.zones.api.max_failures,
        }
        if settings.zones.api is not None
        else None,
        file_path=settings.zones.file_path,
        cache_ttl_sec=settings.zones.api.cache_ttl_sec if settings.zones.api else 30.0,
    )


def main() -> None:
    # 메인 실행 흐름
    args = _parse_args()
    if args.video and args.source_type in ("rtsp", "plugin"):
        raise ValueError("--video cannot be combined with --source-type rtsp/plugin")

    root_dir = resolve_project_root()
    log_dir = root_dir / "outputs" / "logs"
    settings = load_pipeline_settings(
        camera_id=args.camera_id,
        video_override=args.video,
        source_type_override=args.source_type,
    )
    setup_logging(
        str(log_dir),
        level=settings.logging.level,
        fmt=settings.logging.format,
        file_suffix=settings.camera_id,
        max_bytes=settings.logging.max_bytes,
        backup_count=settings.logging.backup_count,
    )
    set_log_context(camera_id=settings.camera_id, source_type=settings.source.type)

    # 스냅샷 저장 경로 사전 검증
    snapshot_base_dir = settings.events.snapshot_base_dir
    if snapshot_base_dir:
        try:
            Path(snapshot_base_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"snapshot base dir not writable: {exc}") from exc

    # webcam index 해석 우선순위:
    # CLI(--camera-index) > camera config(source.index) > 0
    resolved_camera_index = args.camera_index
    if resolved_camera_index is None:
        resolved_camera_index = settings.source.index
    if resolved_camera_index is None:
        resolved_camera_index = 0

    source = _build_source(
        settings.source.type, args.video, settings.source.path,
        settings.source.url, settings.source.adapter, resolved_camera_index, settings.rtsp, loop=args.loop,
    )
    # 라이브 소스는 스레드 래퍼로 감싸서 프레임 지연/깨짐 방지
    if source.is_live:
        from ai.pipeline.sources.threaded import ThreadedSource
        source = ThreadedSource(source)
    sampler = FrameSampler(settings.ingest.fps_limit, source.fps())
    metrics = MetricsTracker(settings.metrics.interval_sec, settings.metrics.fps_window_sec) if settings.metrics.enabled else None
    builder = _build_event_builder(settings, snapshot_base_dir)
    sensor_runtime = _build_sensor_runtime(settings, metrics)
    if sensor_runtime is not None:
        # 의도: 센서 lane은 이벤트 생성 경계에서만 결합해 코어 변경 범위를 최소화한다.
        builder = SensorAwareEventBuilder(
            builder,
            sensor_runtime,
            settings.sensor.time_window_ms,
            emit_fused_events=settings.sensor.emit_fused_events,
            fusion_callback=metrics.on_fusion_attempt if metrics is not None else None,
        )
    sensor_event_builder = (
        SensorEventBuilder(settings.site_id, settings.camera_id, settings.timezone)
        if sensor_runtime is not None
        else None
    )
    emitter = _build_emitter(settings, args, metrics)

    dedup = DedupController(
        cooldown_sec=settings.dedup.cooldown_sec,
        prune_interval=settings.dedup.prune_interval,
    ) if settings.dedup.enabled else None

    if sensor_runtime is not None:
        sensor_adapter_count = len(_resolve_sensor_adapter_paths(settings))
        sensor_runtime.start()
        logger.info(
            "sensor lane enabled (adapters=%d, type=%s, topic=%s, window_ms=%d, emit_events=%s, emit_fused_events=%s)",
            sensor_adapter_count,
            settings.sensor.type or "sensor",
            settings.sensor.topic or "-",
            settings.sensor.time_window_ms,
            settings.sensor.emit_events,
            settings.sensor.emit_fused_events,
        )

    try:
        ctx = PipelineContext(
            source=source,
            sampler=sampler,
            event_builder=builder,
            emitter=emitter,
            zone_evaluator=_build_zone_evaluator(settings),
            dedup=dedup,
            metrics=metrics,
            heartbeat=Heartbeat(settings.heartbeat.interval_sec) if settings.heartbeat.enabled else None,
            visualizer=OpencvVisualizer(window_name=f"AI Pipeline - {settings.camera_id}") if args.visualize else None,
            sensor_runtime=sensor_runtime,
            sensor_event_builder=sensor_event_builder,
            sensor_emit_events=settings.sensor.emit_events,
        )
    except Exception:
        if sensor_runtime is not None:
            sensor_runtime.stop()
        raise

    settings_payload = asdict(settings)
    src_url = settings_payload.get("source", {}).get("url")
    if src_url:
        settings_payload["source"]["url"] = mask_url(src_url)
    post_url = settings_payload.get("events", {}).get("post_url")
    if post_url:
        settings_payload["events"]["post_url"] = mask_url(post_url)
    logger.info("pipeline_settings=%s", settings_payload)

    pipeline = Pipeline(ctx)

    def _on_shutdown(signum, _frame):
        sig_name = signal.Signals(signum).name
        logger.info("received %s, requesting graceful shutdown", sig_name)
        pipeline.request_stop()

    signal.signal(signal.SIGTERM, _on_shutdown)
    signal.signal(signal.SIGINT, _on_shutdown)

    pipeline.run(max_events=args.max_events)


if __name__ == "__main__":
    main()
