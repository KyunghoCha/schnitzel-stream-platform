# Docs: docs/implementation/60-observability/metrics/spec.md
from __future__ import annotations

# 간단 메트릭/하트비트 유틸
# - fps, drops, events(accepted), backend ack, errors 카운트
# - 일정 주기마다 스냅샷 로깅

from collections import deque
from dataclasses import dataclass, field
import threading
import time
from typing import Any


def build_metrics_log(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "uptime_sec": snapshot.get("uptime_sec"),
        "fps": snapshot.get("fps"),
        "frames": snapshot.get("frames"),
        "drops": snapshot.get("drops"),
        "events": snapshot.get("events"),
        "events_accepted": snapshot.get("events_accepted"),
        "backend_ack_ok": snapshot.get("backend_ack_ok"),
        "backend_ack_fail": snapshot.get("backend_ack_fail"),
        "errors": snapshot.get("errors"),
        "sensor_packets_total": snapshot.get("sensor_packets_total"),
        "sensor_packets_dropped": snapshot.get("sensor_packets_dropped"),
        "sensor_source_errors": snapshot.get("sensor_source_errors"),
        "fusion_attempts": snapshot.get("fusion_attempts"),
        "fusion_hits": snapshot.get("fusion_hits"),
        "fusion_misses": snapshot.get("fusion_misses"),
    }


@dataclass
class MetricsTracker:
    # 메트릭 추적기
    interval_sec: float = 10.0
    fps_window_sec: float = 5.0
    _start_ts: float = field(default_factory=time.monotonic, init=False)
    _last_log_ts: float = field(default_factory=time.monotonic, init=False)
    _frame_ts: deque[float] = field(default_factory=deque, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    frames: int = 0
    drops: int = 0
    # accepted count at emitter boundary (emit() returned True)
    events: int = 0
    # backend delivery result count (only meaningful for BackendEmitter path)
    backend_ack_ok: int = 0
    backend_ack_fail: int = 0
    errors: int = 0
    sensor_packets_total: int = 0
    sensor_packets_dropped: int = 0
    sensor_source_errors: int = 0
    fusion_attempts: int = 0
    fusion_hits: int = 0
    fusion_misses: int = 0

    def on_frame(self) -> None:
        # 프레임 처리 시 호출
        now = time.monotonic()
        with self._lock:
            self.frames += 1
            self._frame_ts.append(now)
            # fps 계산을 위해 윈도우 밖 타임스탬프 제거
            cutoff = now - self.fps_window_sec
            while self._frame_ts and self._frame_ts[0] < cutoff:
                self._frame_ts.popleft()

    def on_drop(self) -> None:
        # 드롭 발생 시 호출
        with self._lock:
            self.drops += 1

    def on_event(self) -> None:
        # 이벤트 수락(emit=True) 시 호출
        with self._lock:
            self.events += 1

    def on_backend_ack(self, ok: bool) -> None:
        # 백엔드 전달 결과(ACK)를 별도 집계한다.
        with self._lock:
            if ok:
                self.backend_ack_ok += 1
            else:
                self.backend_ack_fail += 1

    def on_error(self) -> None:
        # 에러 발생 시 호출
        with self._lock:
            self.errors += 1

    def on_sensor_packet(self) -> None:
        with self._lock:
            self.sensor_packets_total += 1

    def on_sensor_drop(self) -> None:
        with self._lock:
            self.sensor_packets_dropped += 1

    def on_sensor_error(self) -> None:
        with self._lock:
            self.sensor_source_errors += 1

    def on_fusion_attempt(self, hit: bool) -> None:
        with self._lock:
            self.fusion_attempts += 1
            if hit:
                self.fusion_hits += 1
            else:
                self.fusion_misses += 1

    def should_log(self) -> bool:
        # 로그 출력 시점 판단
        with self._lock:
            return (time.monotonic() - self._last_log_ts) >= self.interval_sec

    def snapshot(self) -> dict[str, Any]:
        # 현재 메트릭 스냅샷
        with self._lock:
            now = time.monotonic()
            fps = len(self._frame_ts) / max(1e-6, self.fps_window_sec)
            uptime = now - self._start_ts
            self._last_log_ts = now
            return {
                "uptime_sec": round(uptime, 3),
                "fps": round(fps, 3),
                "frames": self.frames,
                "drops": self.drops,
                "events": self.events,
                "events_accepted": self.events,
                "backend_ack_ok": self.backend_ack_ok,
                "backend_ack_fail": self.backend_ack_fail,
                "errors": self.errors,
                "sensor_packets_total": self.sensor_packets_total,
                "sensor_packets_dropped": self.sensor_packets_dropped,
                "sensor_source_errors": self.sensor_source_errors,
                "fusion_attempts": self.fusion_attempts,
                "fusion_hits": self.fusion_hits,
                "fusion_misses": self.fusion_misses,
            }


@dataclass
class Heartbeat:
    # 하트비트 로거
    interval_sec: float = 15.0
    _start_ts: float = field(default_factory=time.monotonic, init=False)
    _last_log_ts: float = field(default_factory=time.monotonic, init=False)

    def should_log(self) -> bool:
        return (time.monotonic() - self._last_log_ts) >= self.interval_sec

    def snapshot(
        self,
        last_frame_ts: float | None,
        camera_id: str | None = None,
        sensor_last_packet_age_sec: float | None = None,
    ) -> dict[str, Any]:
        now = time.monotonic()
        uptime = now - self._start_ts
        self._last_log_ts = now
        last_frame_age_sec = None
        if last_frame_ts is not None:
            last_frame_age_sec = round(max(0.0, now - last_frame_ts), 3)
        return {
            "uptime_sec": round(uptime, 3),
            "last_frame_age_sec": last_frame_age_sec,
            "sensor_last_packet_age_sec": sensor_last_packet_age_sec,
            "camera_id": camera_id,
        }
