# Docs: docs/implementation/10-rtsp-stability/README.md
from __future__ import annotations

# RTSP 스트림 프레임 소스 (재연결 로직 포함)

from dataclasses import dataclass
import logging
import random
import time
import os
import cv2

from ai.utils.urls import mask_url

logger = logging.getLogger(__name__)

_INIT_MAX_ATTEMPTS = 3  # __post_init__ 시 무한 재시도 방지 최대 횟수
_RECENT_RECONNECT_DELAY = 0.2  # 최근 재연결 직후 짧은 대기 (초)


@dataclass
class RtspSource:
    """RTSP 기반 VideoCapture (자동 재연결 지원)"""

    url: str
    timeout_sec: float = 5.0
    base_delay_sec: float = 0.5
    max_delay_sec: float = 10.0
    max_attempts: int = 0  # 0이면 무한 재시도
    jitter_ratio: float = 0.2
    transport: str = "tcp"  # tcp | udp
    supports_reconnect: bool = True

    _attempt: int = 0
    _last_frame_ts: float | None = None
    _fatal_failure: bool = False
    _recent_reconnect: bool = False
    errors: int = 0
    reconnects: int = 0

    def __post_init__(self) -> None:
        if not self._connect_with_retry(raise_on_fail=True):
            raise RuntimeError(f"Cannot open RTSP stream: {mask_url(self.url)}")

    def read(self) -> tuple[bool, object]:
        if self._fatal_failure:
            return False, None
        if not self.cap or not self.cap.isOpened():
            ok = self._connect_with_retry(raise_on_fail=False)
            if not ok and self._fatal_failure:
                return False, None
            ret, frame = self.cap.read()
            if ret:
                self._last_frame_ts = time.monotonic()
                self._recent_reconnect = False
            return ret, frame

        ret, frame = self.cap.read()
        now = time.monotonic()

        if ret:
            self._last_frame_ts = now
            self._recent_reconnect = False
            return ret, frame

        self.errors += 1
        if self._last_frame_ts is None:
            self._last_frame_ts = now

        if (now - self._last_frame_ts) > self.timeout_sec:
            ok = self._connect_with_retry(raise_on_fail=False)
            if not ok and self._fatal_failure:
                return False, None
            ret, frame = self.cap.read()
            if ret:
                self._last_frame_ts = time.monotonic()
                self._recent_reconnect = False
            return ret, frame

        return ret, frame

    def release(self) -> None:
        self.cap.release()

    def fps(self) -> float:
        return float(self.cap.get(cv2.CAP_PROP_FPS))

    @property
    def is_live(self) -> bool:
        return True

    def _set_ffmpeg_options(self) -> str | None:
        """OPENCV_FFMPEG_CAPTURE_OPTIONS를 설정하고, 이전 값을 반환한다."""
        prev = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{self.transport}"
        return prev

    @staticmethod
    def _restore_ffmpeg_options(prev: str | None) -> None:
        """이전 OPENCV_FFMPEG_CAPTURE_OPTIONS 값을 복원한다."""
        if prev is None:
            os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)
        else:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = prev

    def _connect_with_retry(self, raise_on_fail: bool) -> bool:
        if hasattr(self, "cap") and self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        self._attempt = 0

        # 초기화 시점(raise_on_fail=True)에는 무한 루프 방지 (최대 3회 또는 max_attempts)
        # 런타임에는 설정된 max_attempts(0=무한) 따름
        local_max_attempts = self.max_attempts
        if raise_on_fail and local_max_attempts == 0:
            local_max_attempts = _INIT_MAX_ATTEMPTS

        while True:
            self._attempt += 1
            if self._attempt > 1:
                logger.info(
                    "RTSP reconnecting to %s (attempt %d)",
                    mask_url(self.url), self._attempt,
                )

            # 캡처 생성 직전에 env 설정, 직후 복원 (멀티카메라 race condition 방지)
            prev = self._set_ffmpeg_options()
            try:
                # CAP_FFMPEG 강제 사용 (윈도우에서 MSMF 대신 FFmpeg 백엔드 사용해야 환경변수 옵션이 먹힘)
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            finally:
                self._restore_ffmpeg_options(prev)

            if self.cap.isOpened():
                # 버퍼 사이즈 최소화 (가능한 경우)
                try:
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
                except Exception:
                    pass

                self.reconnects += 1
                self._last_frame_ts = time.monotonic()
                self._recent_reconnect = True
                return True

            # 실패 시 자원 해제
            self.cap.release()

            if local_max_attempts > 0 and self._attempt >= local_max_attempts:
                if raise_on_fail:
                    # 초기화 실패는 즉시 에러 전파
                    return False
                self._fatal_failure = True
                self.supports_reconnect = False
                return False

            delay = min(self.max_delay_sec, self.base_delay_sec * (2 ** (self._attempt - 1)))
            jitter = delay * self.jitter_ratio
            sleep_time = delay + random.uniform(-jitter, jitter)
            time.sleep(sleep_time)

    def recent_reconnect(self) -> bool:
        if self._recent_reconnect:
            self._recent_reconnect = False
            return True
        return False
