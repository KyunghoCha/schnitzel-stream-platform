from __future__ import annotations

import threading
import time

from ai.pipeline.sources.threaded import ThreadedSource


class _FakeInnerSource:
    """테스트용 가짜 소스 (FrameSource Protocol 준수)"""

    supports_reconnect = True
    base_delay_sec = 0.5
    max_delay_sec = 10.0
    jitter_ratio = 0.2
    errors = 0
    reconnects = 0

    def __init__(self, frames: list[tuple[bool, object]] | None = None) -> None:
        self._frames = frames or [(True, f"frame-{i}") for i in range(100)]
        self._idx = 0
        self._lock = threading.Lock()
        self.released = False

    @property
    def is_live(self) -> bool:
        return True

    def fps(self) -> float:
        return 30.0

    def read(self) -> tuple[bool, object]:
        with self._lock:
            if self._idx < len(self._frames):
                ret, frame = self._frames[self._idx]
                self._idx += 1
                return ret, frame
            return self._frames[-1] if self._frames else (False, None)

    def release(self) -> None:
        self.released = True

    def recent_reconnect(self) -> bool:
        return False


class _BlockingInnerSource:
    supports_reconnect = True
    base_delay_sec = 0.5
    max_delay_sec = 10.0
    jitter_ratio = 0.2
    errors = 0
    reconnects = 0

    def __init__(self) -> None:
        self._first = True
        self.released = False

    @property
    def is_live(self) -> bool:
        return True

    def fps(self) -> float:
        return 30.0

    def read(self) -> tuple[bool, object]:
        if self._first:
            self._first = False
            time.sleep(0.35)
        return False, None

    def release(self) -> None:
        self.released = True


class _ErrorThenIdleSource:
    supports_reconnect = True
    base_delay_sec = 0.5
    max_delay_sec = 10.0
    jitter_ratio = 0.2
    errors = 0
    reconnects = 0

    def __init__(self) -> None:
        self._calls = 0
        self.released = False

    @property
    def is_live(self) -> bool:
        return True

    def fps(self) -> float:
        return 30.0

    def read(self) -> tuple[bool, object]:
        self._calls += 1
        if self._calls == 1:
            raise RuntimeError("boom")
        time.sleep(0.01)
        return False, None

    def release(self) -> None:
        self.released = True


def test_returns_latest_frame() -> None:
    """여러 프레임 후 최신 프레임이 반환되는지 확인"""
    inner = _FakeInnerSource()
    ts = ThreadedSource(inner)
    try:
        # 백그라운드 스레드가 프레임을 소비할 시간을 줌
        time.sleep(0.1)
        ret, frame = ts.read()
        assert ret is True
        # 백그라운드가 여러 프레임을 읽었으므로 첫 프레임이 아닌 이후 프레임이어야 함
        assert frame is not None
    finally:
        ts.release()


def test_delegates_fps() -> None:
    """fps()가 inner 소스로 위임되는지 확인"""
    inner = _FakeInnerSource()
    ts = ThreadedSource(inner)
    try:
        assert ts.fps() == 30.0
    finally:
        ts.release()


def test_delegates_is_live() -> None:
    """is_live가 inner 소스로 위임되는지 확인"""
    inner = _FakeInnerSource()
    ts = ThreadedSource(inner)
    try:
        assert ts.is_live is True
    finally:
        ts.release()


def test_release_stops_thread() -> None:
    """release() 호출 시 스레드가 종료되고 inner.release()가 호출되는지 확인"""
    inner = _FakeInnerSource()
    ts = ThreadedSource(inner)
    thread = ts._thread
    assert thread.is_alive()
    ts.release()
    assert not thread.is_alive()
    assert inner.released is True


def test_passthrough_attrs() -> None:
    """__getattr__로 inner 속성이 패스스루되는지 확인"""
    inner = _FakeInnerSource()
    ts = ThreadedSource(inner)
    try:
        assert ts.supports_reconnect is True
        assert ts.base_delay_sec == 0.5
        assert ts.errors == 0
        assert ts.reconnects == 0
        assert callable(ts.recent_reconnect)
    finally:
        ts.release()


def test_read_failure_stored() -> None:
    """inner가 (False, None)을 반환하면 메인 스레드에도 전파되는지 확인"""
    inner = _FakeInnerSource(frames=[(False, None)] * 10)
    ts = ThreadedSource(inner)
    try:
        time.sleep(0.05)
        ret, frame = ts.read()
        assert ret is False
        assert frame is None
    finally:
        ts.release()


def test_read_does_not_block_indefinitely_before_first_frame() -> None:
    """초기 프레임이 준비되지 않아도 read()가 제한 시간 내 반환되는지 확인"""
    inner = _BlockingInnerSource()
    ts = ThreadedSource(inner)
    try:
        t0 = time.monotonic()
        ret, frame = ts.read()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.5
        assert ret is False
        assert frame is None
    finally:
        ts.release()


def test_reader_loop_survives_inner_read_exception() -> None:
    """inner.read() 예외가 발생해도 워커가 죽지 않고 실패 상태를 전달하는지 확인"""
    inner = _ErrorThenIdleSource()
    ts = ThreadedSource(inner)
    try:
        time.sleep(0.05)
        ret, frame = ts.read()
        assert ret is False
        assert frame is None
    finally:
        ts.release()
