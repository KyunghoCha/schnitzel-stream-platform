# Docs: docs/design/pipeline_design.md, docs/implementation/00-overview/data-flow/spec.md
from __future__ import annotations

# 비동기 프레임 처리 워커 (Display-First)
#
# [메인 스레드]  read → submit → get_results → visualize
# [워커 스레드]  inference → _results 즉시 갱신 → zone eval → dedup → emit
#
# 핵심: 추론 직후 display를 즉시 갱신한 뒤 zone/emit을 수행하여,
#       zone API fetch 지연이 시각화 FPS에 영향을 주지 않는다.

import logging
import threading
from typing import Any

from ai.pipeline.events import EventBuilder
from ai.pipeline.emitters import EventEmitter
from ai.rules.dedup import DedupController
from ai.rules.zones import ZoneEvaluator
from ai.utils.metrics import MetricsTracker

logger = logging.getLogger(__name__)


class FrameProcessor:
    """백그라운드 워커 스레드에서 프레임을 처리하여 메인 루프 블로킹을 방지한다.

    [메인 스레드]   submit(frame_idx, frame) → _pending 덮어쓰기 (latest-only)
    [워커 스레드]   _loop() → build(inference) → _results 즉시 갱신 → zone → dedup → emit
    [메인 스레드]   get_results() → 최신 탐지 결과 반환 (논블로킹)
    """

    def __init__(
        self,
        event_builder: EventBuilder,
        emitter: EventEmitter,
        zone_evaluator: ZoneEvaluator | None = None,
        dedup: DedupController | None = None,
        metrics: MetricsTracker | None = None,
    ) -> None:
        self._event_builder = event_builder
        self._emitter = emitter
        self._zone_evaluator = zone_evaluator
        self._dedup = dedup
        self._metrics = metrics

        # latest-only 프레임 버퍼 (메인→워커)
        # 의도: live 모드에서는 "모든 프레임 보존"보다 "최신 프레임 우선"이 운영상 중요하다.
        # 백로그를 허용하지 않아 시각화 지연 누적을 방지한다.
        self._lock = threading.Lock()
        self._pending: tuple[int, Any] | None = None
        self._new_frame = threading.Event()

        # 최신 결과 (워커→메인, display용)
        self._results_lock = threading.Lock()
        self._results: list[dict[str, Any]] = []

        # emit 카운트 (워커에서만 갱신, 메인에서 max_events 체크)
        self._emitted = 0

        # 워커 스레드 제어
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._loop,
            name="frame-processor",
            daemon=True,
        )
        self._thread.start()

    @property
    def emitted(self) -> int:
        """성공적으로 전송된 이벤트 수."""
        return self._emitted

    def submit(self, frame_idx: int, frame: Any) -> None:
        """처리할 프레임을 제출한다 (논블로킹, latest-only 덮어쓰기)."""
        with self._lock:
            self._pending = (frame_idx, frame)
        self._new_frame.set()

    def get_results(self) -> list[dict[str, Any]]:
        """최신 탐지 결과를 반환한다 (논블로킹)."""
        with self._results_lock:
            return list(self._results)

    def stop(self) -> None:
        """워커 스레드를 정지하고 join한다."""
        self._stop.set()
        self._new_frame.set()  # wait에서 깨우기
        self._thread.join(timeout=10)
        if self._thread.is_alive():
            logger.warning("frame processor worker did not finish in time")

    # -- worker loop --------------------------------------------------------

    def _loop(self) -> None:
        """워커 루프: 새 프레임 대기 → 추론 → display 즉시 갱신 → zone → dedup → emit."""
        while not self._stop.is_set():
            self._new_frame.wait()
            if self._stop.is_set():
                break
            self._new_frame.clear()

            # pending 가져오기 (latest-only)
            with self._lock:
                pending = self._pending
                self._pending = None

            if pending is None:
                continue

            frame_idx, frame = pending

            # 1. 추론 (AI 모델 호출)
            payloads = self._event_builder.build(frame_idx, frame)

            # 2. display 결과 즉시 갱신 — zone/emit 완료를 기다리지 않음
            with self._results_lock:
                self._results = payloads

            # 3. 후처리: zone eval → dedup → emit
            emitted = 0
            for payload in payloads:
                if self._zone_evaluator is not None:
                    payload = self._zone_evaluator.apply(payload)
                if self._dedup is not None and not self._dedup.allow_emit(payload):
                    continue
                ok = self._emitter.emit(payload)
                if ok:
                    emitted += 1
                    if self._metrics is not None:
                        self._metrics.on_event()
            self._emitted += emitted
