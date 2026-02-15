# Docs: docs/legacy/design/pipeline_design.md, docs/implementation/00-overview/data-flow/spec.md
from __future__ import annotations

# 파이프라인 코어
# - Source -> Sampler -> Queue -> EventBuilder -> Emitter

from dataclasses import dataclass
import logging
import random
import threading
import time
from typing import Any, TYPE_CHECKING

from ai.pipeline.sampler import FrameSampler
from ai.pipeline.sources import FrameSource
from ai.pipeline.events import EventBuilder
from ai.pipeline.emitters import EventEmitter
from ai.pipeline.processor import FrameProcessor
from ai.rules.dedup import DedupController
from ai.rules.zones import ZoneEvaluator
from ai.utils.metrics import MetricsTracker, Heartbeat, build_metrics_log
from ai.vision.visualizer import Visualizer

if TYPE_CHECKING:
    from ai.pipeline.sensors.builder import SensorEventBuilder
    from ai.pipeline.sensors.runtime import SensorRuntimeLike

logger = logging.getLogger(__name__)
metrics_logger = logging.getLogger("ai.metrics")
heartbeat_logger = logging.getLogger("ai.heartbeat")

_RECENT_RECONNECT_DELAY = 0.2  # 최근 재연결 직후 짧은 대기 (초)


@dataclass
class PipelineContext:
    # 파이프라인 구성요소 컨테이너
    source: FrameSource
    sampler: FrameSampler
    event_builder: EventBuilder
    emitter: EventEmitter
    zone_evaluator: ZoneEvaluator | None = None
    dedup: DedupController | None = None
    metrics: MetricsTracker | None = None
    heartbeat: Heartbeat | None = None
    visualizer: Visualizer | None = None
    sensor_runtime: SensorRuntimeLike | None = None
    sensor_event_builder: SensorEventBuilder | None = None
    sensor_emit_events: bool = False


class Pipeline:
    def __init__(self, ctx: PipelineContext) -> None:
        self.ctx = ctx
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        """외부에서 파이프라인 종료를 요청한다 (SIGTERM 등)."""
        self._stop_event.set()

    # -- public ---------------------------------------------------------

    def run(self, max_events: int | None = None) -> None:
        # 프레임 루프 실행
        frame_idx = 0
        emitted = 0
        sensor_emitted_total = 0
        last_frame_ts: float | None = None
        consecutive_failures = 0
        last_payloads: list[dict[str, Any]] = []

        # 라이브 소스는 비동기 처리, 파일 소스는 동기 처리
        use_async = self.ctx.source.is_live
        processor: FrameProcessor | None = None
        if use_async:
            processor = FrameProcessor(
                event_builder=self.ctx.event_builder,
                emitter=self.ctx.emitter,
                zone_evaluator=self.ctx.zone_evaluator,
                dedup=self.ctx.dedup,
                metrics=self.ctx.metrics,
            )

        try:
            while not self._stop_event.is_set():
                sensor_new = self._emit_sensor_events()
                emitted += sensor_new
                sensor_emitted_total += sensor_new

                ret, frame = self.ctx.source.read()

                if not ret:
                    action = self._handle_read_failure(consecutive_failures)
                    if action == "stop":
                        break
                    consecutive_failures += 1
                    continue

                consecutive_failures = 0
                last_frame_ts = time.monotonic()
                if self.ctx.metrics is not None:
                    self.ctx.metrics.on_frame()

                # 1. 분석/이벤트 처리
                if self.ctx.sampler.should_sample(frame_idx):
                    if use_async and processor is not None:
                        processor.submit(frame_idx, frame)       # 논블로킹
                    else:
                        new_emitted, last_payloads = self._process_frame(frame_idx, frame)
                        emitted += new_emitted
                else:
                    if self.ctx.metrics is not None:
                        self.ctx.metrics.on_drop()

                # 2. 시각화 (끊김 방지를 위해 매 프레임 수행)
                if self.ctx.visualizer is not None:
                    if use_async and processor is not None:
                        last_payloads = processor.get_results()  # 논블로킹
                    self.ctx.visualizer.show(frame, last_payloads)

                # max_events 체크
                # 주의: 여기서의 emitted는 emitter.emit()의 성공 기준을 따른다.
                # BackendEmitter에서는 "큐 적재 성공" 기준이며, HTTP ACK 기준이 아니다.
                if use_async and processor is not None:
                    total = processor.emitted + sensor_emitted_total
                else:
                    total = emitted
                if max_events is not None and total >= max_events:
                    break

                frame_idx += 1

                # 3. 하트비트 / 메트릭 로깅
                self._emit_telemetry(last_frame_ts)

                # 4. 재생 속도 조절 (파일 소스에만)
                self._throttle(last_frame_ts)
        finally:
            if processor is not None:
                processor.stop()
            self._cleanup()

    # -- private --------------------------------------------------------

    def _handle_read_failure(self, consecutive_failures: int) -> str:
        """프레임 읽기 실패 시 재시도 또는 중지 결정. 'stop'이면 루프 종료."""
        if not self.ctx.source.supports_reconnect:
            return "stop"
        if self.ctx.metrics is not None:
            self.ctx.metrics.on_error()
        recent_reconnect = getattr(self.ctx.source, "recent_reconnect", None)
        if callable(recent_reconnect) and recent_reconnect():
            time.sleep(_RECENT_RECONNECT_DELAY)
            return "retry"
        delay = self._retry_delay(consecutive_failures + 1)
        logger.warning("frame_read_failed retrying in %.2fs", delay)
        time.sleep(delay)
        return "retry"

    def _process_frame(self, frame_idx: int, frame: Any) -> tuple[int, list[dict[str, Any]]]:
        """프레임에서 이벤트를 생성/필터/전송한다. (emitted_count, payloads) 반환."""
        payloads = self.ctx.event_builder.build(frame_idx, frame)
        emitted = 0
        for payload in payloads:
            if self.ctx.zone_evaluator is not None:
                payload = self.ctx.zone_evaluator.apply(payload)
            if self.ctx.dedup is not None and not self.ctx.dedup.allow_emit(payload):
                continue
            ok = self.ctx.emitter.emit(payload)
            if ok:
                emitted += 1
                if self.ctx.metrics is not None:
                    self.ctx.metrics.on_event()
        return emitted, payloads

    def _emit_telemetry(self, last_frame_ts: float | None) -> None:
        """메트릭 로깅 + 하트비트 발행."""
        if self.ctx.metrics is not None and self.ctx.metrics.should_log():
            metrics_logger.info("metrics", extra={"metrics": build_metrics_log(self.ctx.metrics.snapshot())})
        if self.ctx.heartbeat is not None and self.ctx.heartbeat.should_log():
            sensor_age = None
            if self.ctx.sensor_runtime is not None:
                sensor_age = self.ctx.sensor_runtime.last_packet_age_sec()
            heartbeat_logger.info(
                "heartbeat",
                extra={
                    "heartbeat": self.ctx.heartbeat.snapshot(
                        last_frame_ts,
                        sensor_last_packet_age_sec=sensor_age,
                    )
                },
            )

    def _emit_sensor_events(self) -> int:
        """센서 런타임 outbox를 독립 sensor_event로 전송한다."""
        if (
            self.ctx.sensor_runtime is None
            or self.ctx.sensor_event_builder is None
            or not self.ctx.sensor_emit_events
        ):
            return 0
        packets = self.ctx.sensor_runtime.drain_packets()
        if not packets:
            return 0
        payloads = self.ctx.sensor_event_builder.build(packets)
        emitted = 0
        for payload in payloads:
            # 의도: SENSOR_EVENT는 원시 센서 관측 보존용이므로 zone/dedup 규칙을 적용하지 않는다.
            ok = self.ctx.emitter.emit(payload)
            if ok:
                emitted += 1
                if self.ctx.metrics is not None:
                    self.ctx.metrics.on_event()
        return emitted

    def _throttle(self, last_frame_ts: float | None) -> None:
        """파일 소스인 경우 FPS에 맞춰 재생 속도를 조절한다."""
        if self.ctx.source.is_live or last_frame_ts is None:
            return
        source_fps = self.ctx.source.fps()
        if source_fps > 0:
            expected_duration = 1.0 / source_fps
            elapsed = time.monotonic() - last_frame_ts
            sleep_time = expected_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _cleanup(self) -> None:
        """파이프라인 리소스 해제."""
        if self.ctx.sensor_runtime is not None:
            self.ctx.sensor_runtime.stop()
        self.ctx.emitter.close()
        if self.ctx.visualizer is not None:
            self.ctx.visualizer.close()
        self.ctx.source.release()

    def _retry_delay(self, failures: int) -> float:
        base = float(getattr(self.ctx.source, "base_delay_sec", 0.5))
        max_delay = float(getattr(self.ctx.source, "max_delay_sec", 10.0))
        jitter_ratio = float(getattr(self.ctx.source, "jitter_ratio", 0.2))
        delay = min(max_delay, base * (2 ** max(0, failures - 1)))
        jitter = delay * jitter_ratio
        return max(0.0, delay + random.uniform(-jitter, jitter))
