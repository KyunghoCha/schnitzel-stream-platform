from __future__ import annotations

from dataclasses import dataclass
import logging
import queue
import threading
from typing import Any, Callable

from ai.clients.backend_api import BackendClient, BackendClientConfig

logger = logging.getLogger(__name__)

_SENTINEL = object()  # 큐 종료 신호


@dataclass
class BackendEmitter:
    # 백엔드 전송 에미터 (비동기 큐 기반)
    config: BackendClientConfig
    queue_size: int = 256
    delivery_callback: Callable[[bool], None] | None = None

    def __post_init__(self) -> None:
        self.client = BackendClient(self.config)
        self._queue: queue.Queue = queue.Queue(maxsize=self.queue_size)
        self._worker = threading.Thread(target=self._drain, daemon=True, name="backend-emitter")
        self._worker.start()

    def _drain(self) -> None:
        """백그라운드 스레드: 큐에서 페이로드를 꺼내 전송."""
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                self._queue.task_done()
                break
            delivered = False
            try:
                delivered = self.client.post_event(item)
            except Exception:
                logger.exception("unexpected error in backend emitter worker")
            finally:
                # 의도: 수락(emit=True)과 실제 백엔드 전달 결과를 분리 계측한다.
                # callback은 worker 경계에서 정확히 1회 호출된다.
                if self.delivery_callback is not None:
                    try:
                        self.delivery_callback(delivered)
                    except Exception:
                        logger.exception("backend delivery callback failed")
                self._queue.task_done()

    def emit(self, payload: dict[str, Any]) -> bool:
        # 큐에 넣기 (non-blocking). 큐가 가득 차면 drop + 경고.
        # 의도: 반환값 True는 "백엔드 최종 전달 성공"이 아니라
        # "에미터 경계(큐)에서 수락됨"을 의미한다.
        # 이렇게 해야 ingest 루프를 네트워크 I/O에 묶지 않고 저지연을 유지할 수 있다.
        try:
            self._queue.put_nowait(payload)
            return True
        except queue.Full:
            logger.warning(
                "backend send queue full, dropping event",
                extra={
                    "event_id": payload.get("event_id"),
                    "error_code": "BACKEND_QUEUE_FULL",
                },
            )
            return False

    def close(self) -> None:
        # 종료 신호 전송 후 워커 스레드 대기
        self._queue.put(_SENTINEL)
        self._worker.join(timeout=10.0)
        if self._worker.is_alive():
            logger.warning("backend emitter worker did not finish in time")
