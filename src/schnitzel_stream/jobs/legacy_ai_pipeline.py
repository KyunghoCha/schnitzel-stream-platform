from __future__ import annotations

"""
Legacy AI pipeline job.

Intent:
- Phase 0 strangler migration runs the existing `ai.pipeline` runtime through the new platform entrypoint.
- This preserves a reliable foundation while the new StreamPacket/DAG architecture is still evolving.
- We intentionally avoid importing `ai.pipeline.__main__` to keep the legacy CLI removable.
"""

import argparse
from dataclasses import asdict
import logging
from pathlib import Path
import signal
import socket
import threading
from typing import Any
from urllib.parse import urlparse

from ai.clients.backend_api import BackendClientConfig
from ai.logging_setup import setup_logging, set_log_context
from ai.pipeline.config import load_pipeline_settings, PipelineSettings, RtspSettings, resolve_project_root
from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.emitters import BackendEmitter, FileEmitter, StdoutEmitter, EventEmitter, load_event_emitter
from ai.pipeline.events import MockModelEventBuilder, RealModelEventBuilder, EventBuilder
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

from schnitzel_stream.graph.spec import GraphSpec
from schnitzel_stream.plugins.registry import PluginPolicy

logger = logging.getLogger(__name__)


class _ThreadSafeEmitter:
    """Serialize `emit()`/`close()` calls.

    Intent:
    - Legacy pipeline may call `emit()` from multiple threads (async frame worker + sensor emission).
    - Many emitters are not guaranteed thread-safe (e.g., file writes).
    - A narrow lock here preserves correctness without forcing all emitters to implement locking.
    """

    def __init__(self, inner: EventEmitter) -> None:
        self._inner = inner
        self._lock = threading.Lock()

    def emit(self, payload: dict[str, Any]) -> bool:
        with self._lock:
            return self._inner.emit(payload)

    def close(self) -> None:
        with self._lock:
            self._inner.close()


def _resolve_sample_video() -> str:
    # data/samples/*.mp4 중 첫 번째 파일 선택
    sample_dir = resolve_project_root() / "data" / "samples"
    mp4s = sorted(sample_dir.glob("*.mp4"))
    if not mp4s:
        raise FileNotFoundError(f"No mp4 files under: {sample_dir}")
    return str(mp4s[0])


def _build_source(
    policy: PluginPolicy,
    source_type: str,
    video_override: str | None,
    source_path: str | None,
    source_url: str | None,
    source_adapter: str | None,
    camera_index: int,
    rtsp_cfg: RtspSettings | None,
    loop: bool = False,
):
    if source_type == "plugin":
        adapter_path = (source_adapter or "").strip()
        if not adapter_path:
            raise RuntimeError(
                "plugin source requires source.adapter / AI_SOURCE_ADAPTER (module:ClassName)",
            )
        policy.ensure_path_allowed(adapter_path)
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

    # file
    if video_override is not None:
        if not Path(video_override).exists():
            raise FileNotFoundError(f"video file not found: {video_override}")
        path = video_override
    else:
        path = source_path
        if path and not Path(path).exists():
            # Intent: dev convenience. Broken config path should not block local validation.
            logger.warning("configured source path not found: %s, falling back to sample video", path)
            path = None
        path = path or _resolve_sample_video()
    return FileSource(path, loop=loop)


def _build_event_builder(policy: PluginPolicy, settings: PipelineSettings, snapshot_base_dir: str | None) -> EventBuilder:
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
                "model.mode=real requires AI_MODEL_ADAPTER (e.g., ai.vision.adapters.yolo_adapter:YOLOAdapter)",
            )
        # multi-adapter path is comma-separated; enforce allowlist per item.
        for item in [p.strip() for p in adapter_path.split(",") if p.strip()]:
            policy.ensure_path_allowed(item)
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
    policy: PluginPolicy,
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
        policy.ensure_path_allowed(adapter_path)
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
    policy: PluginPolicy,
    settings: PipelineSettings,
    args: argparse.Namespace,
    metrics: MetricsTracker | None = None,
) -> EventEmitter:
    # Precedence: jsonl > dry-run > custom emitter plugin > backend
    if args.output_jsonl:
        return FileEmitter(args.output_jsonl)
    if args.dry_run:
        return StdoutEmitter()

    emitter_adapter_path = (getattr(settings.events, "emitter_adapter", None) or "").strip()
    if emitter_adapter_path:
        policy.ensure_path_allowed(emitter_adapter_path)
        return load_event_emitter(emitter_adapter_path)

    masked_post_url = mask_url(settings.events.post_url)
    host = urlparse(settings.events.post_url).hostname
    if not host:
        logger.warning("invalid post_url (no host): %s, falling back to dry-run", masked_post_url)
        return StdoutEmitter()
    try:
        socket.gethostbyname(host)
    except socket.gaierror:
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


class LegacyAIPipelineJob:
    """Job entrypoint referenced by `configs/graphs/legacy_pipeline.yaml`."""

    def run(self, spec: GraphSpec, args: argparse.Namespace) -> None:
        # Validate incompatible args early.
        if args.video and args.source_type in ("rtsp", "plugin"):
            raise ValueError("--video cannot be combined with --source-type rtsp/plugin")

        policy = PluginPolicy.from_env()

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

        # Snapshot base dir preflight.
        snapshot_base_dir = settings.events.snapshot_base_dir
        if snapshot_base_dir:
            try:
                Path(snapshot_base_dir).mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise RuntimeError(f"snapshot base dir not writable: {exc}") from exc

        # webcam index priority:
        # CLI(--camera-index) > camera config(source.index) > 0
        resolved_camera_index = args.camera_index
        if resolved_camera_index is None:
            resolved_camera_index = settings.source.index
        if resolved_camera_index is None:
            resolved_camera_index = 0

        source = _build_source(
            policy,
            settings.source.type,
            args.video,
            settings.source.path,
            settings.source.url,
            settings.source.adapter,
            resolved_camera_index,
            settings.rtsp,
            loop=args.loop,
        )

        # Live sources are wrapped to decouple capture from inference.
        if source.is_live:
            from ai.pipeline.sources.threaded import ThreadedSource

            source = ThreadedSource(source)

        sampler = FrameSampler(settings.ingest.fps_limit, source.fps())
        metrics = (
            MetricsTracker(settings.metrics.interval_sec, settings.metrics.fps_window_sec)
            if settings.metrics.enabled
            else None
        )

        builder = _build_event_builder(policy, settings, snapshot_base_dir)

        sensor_runtime = _build_sensor_runtime(policy, settings, metrics)
        if sensor_runtime is not None:
            # Intent: keep sensor fusion at the builder boundary for minimal blast radius.
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

        emitter: EventEmitter = _build_emitter(policy, settings, args, metrics)
        emitter = _ThreadSafeEmitter(emitter)

        dedup = (
            DedupController(
                cooldown_sec=settings.dedup.cooldown_sec,
                prune_interval=settings.dedup.prune_interval,
            )
            if settings.dedup.enabled
            else None
        )

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

        # Log effective settings (mask secrets/urls).
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
