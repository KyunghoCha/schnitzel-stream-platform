# Docs: docs/legacy/specs/legacy_pipeline_spec.md, docs/implementation/10-rtsp-stability/README.md
from __future__ import annotations

# 라이브 소스 스레드 분리 래퍼
# - 백그라운드 스레드로 read() 연속 호출, 최신 프레임만 보관
# - 모델 추론 중 프레임 수신 지연/깨짐 방지

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)
_FIRST_FRAME_WAIT_SEC = 0.2


class ThreadedSource:
    """백그라운드 스레드로 프레임을 연속 수신하고, 메인 스레드에서 최신 프레임만 반환하는 래퍼.

    [백그라운드 스레드]  _inner.read() → _latest 덮어쓰기 (반복)
    [메인 스레드]        read() → _latest 반환 (즉시)
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._first_ready = threading.Event()
        self._latest: tuple[bool, Any] = (False, None)

        self._thread = threading.Thread(
            target=self._reader_loop,
            name="threaded-frame-reader",
            daemon=True,
        )
        self._thread.start()

    # -- FrameSource protocol ------------------------------------------------

    @property
    def is_live(self) -> bool:
        return self._inner.is_live

    def fps(self) -> float:
        return self._inner.fps()

    def read(self) -> tuple[bool, Any]:
        if self._stop.is_set():
            return False, None
        # 의도: 초기 프레임 준비 지연이 전체 파이프라인을 멈추지 않도록 한다.
        # 준비되지 않은 경우 (False, None)을 반환해 상위 재시도 정책에 위임한다.
        if not self._first_ready.wait(timeout=_FIRST_FRAME_WAIT_SEC):
            return False, None
        with self._lock:
            return self._latest

    def release(self) -> None:
        self._stop.set()
        self._first_ready.set()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            logger.warning("threaded frame reader did not stop in time")
        self._inner.release()

    # -- passthrough for reconnect attrs etc. --------------------------------

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    # -- background reader ---------------------------------------------------

    def _reader_loop(self) -> None:
        # 의도: 최신 프레임만 유지(latest-only)하여 라이브 스트림 지연 누적을 막는다.
        # 오래된 프레임은 자연스럽게 덮어써 버린다.
        while not self._stop.is_set():
            try:
                ret, frame = self._inner.read()
            except Exception as exc:
                # 의도: source.read() 예외가 워커 스레드를 죽이지 않도록 보호한다.
                logger.warning("threaded source read failed: %s", exc)
                ret, frame = False, None
            with self._lock:
                self._latest = (ret, frame)
            if not self._first_ready.is_set():
                self._first_ready.set()
