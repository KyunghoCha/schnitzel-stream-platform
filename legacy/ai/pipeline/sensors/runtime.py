from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import random
import threading
import time
from typing import Any, Callable, Protocol

from ai.pipeline.sensors.protocol import SensorSource

logger = logging.getLogger(__name__)

_MIN_RETRY_SEC = 0.2


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


@dataclass(frozen=True)
class SensorPacket:
    sensor_id: str
    sensor_type: str
    source_ts: datetime | None
    ingest_ts: datetime
    payload: dict[str, Any]

    @property
    def event_ts(self) -> datetime:
        return self.source_ts or self.ingest_ts

    def to_event_payload(self) -> dict[str, Any]:
        out = dict(self.payload)
        out.setdefault("sensor_id", self.sensor_id)
        out.setdefault("sensor_type", self.sensor_type)
        out.setdefault("sensor_ts", self.source_ts.isoformat() if self.source_ts is not None else None)
        out.setdefault("ingest_ts", self.ingest_ts.isoformat())
        return out


class SensorRuntimeLike(Protocol):
    """센서 런타임 최소 인터페이스."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def latest_for_event(self, event_ts: str | None, time_window_ms: int) -> dict[str, Any] | None: ...

    def drain_packets(self, limit: int | None = None) -> list[SensorPacket]: ...

    def last_packet_ts(self) -> datetime | None: ...

    def last_packet_age_sec(self) -> float | None: ...


def _normalize_sensor_packet(
    raw: Any,
    sensor_type_hint: str | None,
    topic_hint: str | None,
) -> SensorPacket:
    ingest_ts = _utc_now()
    if isinstance(raw, dict):
        payload = dict(raw)
    else:
        payload = {"value": raw}

    sensor_id_raw = payload.get("sensor_id") or payload.get("id") or topic_hint or "sensor"
    sensor_type_raw = payload.get("sensor_type") or payload.get("type") or sensor_type_hint or "sensor"
    source_ts = _parse_ts(payload.get("sensor_ts") or payload.get("source_ts") or payload.get("ts"))

    return SensorPacket(
        sensor_id=str(sensor_id_raw),
        sensor_type=str(sensor_type_raw),
        source_ts=source_ts,
        ingest_ts=ingest_ts,
        payload=payload,
    )


class SensorRuntime:
    """Background sensor collector with bounded in-memory packet buffer."""

    def __init__(
        self,
        source: SensorSource,
        queue_size: int = 256,
        sensor_type_hint: str | None = None,
        topic_hint: str | None = None,
        on_packet: Callable[[], None] | None = None,
        on_drop: Callable[[], None] | None = None,
        on_error: Callable[[], None] | None = None,
    ) -> None:
        self._source = source
        self._queue_size = max(1, int(queue_size))
        self._sensor_type_hint = sensor_type_hint
        self._topic_hint = topic_hint
        self._on_packet = on_packet
        self._on_drop = on_drop
        self._on_error = on_error

        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._packets: deque[SensorPacket] = deque(maxlen=self._queue_size)
        self._outbox: deque[SensorPacket] = deque(maxlen=self._queue_size)
        self._thread = threading.Thread(target=self._loop, name="sensor-runtime", daemon=True)
        self._started = False
        self._released = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if not self._released:
            self._source.release()
            self._released = True
        if self._started and self._thread.is_alive():
            self._thread.join(timeout=10.0)
            if self._thread.is_alive():
                logger.warning("sensor runtime worker did not finish in time")

    def latest_for_event(self, event_ts: str | None, time_window_ms: int) -> dict[str, Any] | None:
        if time_window_ms <= 0:
            return None

        # 의도: 이벤트 ts가 비어 있거나 파싱 실패해도 파이프라인은 계속 진행한다.
        # 이 경우 현재 시각 기준으로만 근접 매칭을 시도해 hard-fail을 피한다.
        event_dt = _parse_ts(event_ts) or _utc_now()
        window = timedelta(milliseconds=time_window_ms)
        nearest: SensorPacket | None = None
        nearest_delta: timedelta | None = None

        with self._lock:
            packets = list(self._packets)

        for packet in packets:
            delta = abs(packet.event_ts - event_dt)
            if delta > window:
                continue
            if nearest is None or nearest_delta is None or delta < nearest_delta:
                nearest = packet
                nearest_delta = delta

        if nearest is None:
            return None
        return nearest.to_event_payload()

    def drain_packets(self, limit: int | None = None) -> list[SensorPacket]:
        with self._lock:
            if not self._outbox:
                return []
            if limit is None or limit <= 0:
                items = list(self._outbox)
                self._outbox.clear()
                return items
            out: list[SensorPacket] = []
            while self._outbox and len(out) < limit:
                out.append(self._outbox.popleft())
            return out

    def last_packet_ts(self) -> datetime | None:
        with self._lock:
            if not self._packets:
                return None
            return self._packets[-1].event_ts

    def last_packet_age_sec(self) -> float | None:
        ts = self.last_packet_ts()
        if ts is None:
            return None
        age = (_utc_now() - ts).total_seconds()
        return round(max(0.0, age), 3)

    def _loop(self) -> None:
        failures = 0
        while not self._stop.is_set():
            try:
                ok, raw = self._source.read()
            except Exception as exc:
                logger.warning("sensor read failed: %s", exc)
                ok, raw = False, None
                if self._on_error is not None:
                    self._on_error()

            if not ok:
                if not self._source.supports_reconnect:
                    break
                failures += 1
                time.sleep(self._retry_delay(failures))
                continue

            failures = 0
            packet = _normalize_sensor_packet(raw, self._sensor_type_hint, self._topic_hint)
            with self._lock:
                # 독립 SENSOR_EVENT 전송 큐는 latest-first 정책.
                # 과부하 시 오래된 패킷을 버리고 최신 패킷을 우선 유지한다.
                if len(self._outbox) >= self._queue_size:
                    self._outbox.popleft()
                    if self._on_drop is not None:
                        self._on_drop()
                self._packets.append(packet)
                self._outbox.append(packet)
            if self._on_packet is not None:
                self._on_packet()

    def _retry_delay(self, failures: int) -> float:
        base = float(getattr(self._source, "base_delay_sec", _MIN_RETRY_SEC))
        max_delay = float(getattr(self._source, "max_delay_sec", 10.0))
        jitter_ratio = float(getattr(self._source, "jitter_ratio", 0.2))
        delay = min(max_delay, base * (2 ** max(0, failures - 1)))
        jitter = delay * jitter_ratio
        return max(_MIN_RETRY_SEC, delay + random.uniform(-jitter, jitter))


class MultiSensorRuntime:
    """여러 SensorRuntime을 단일 런타임처럼 묶는 합성 런타임."""

    def __init__(self, runtimes: list[SensorRuntime]) -> None:
        if not runtimes:
            raise ValueError("MultiSensorRuntime requires at least one runtime")
        self._runtimes = list(runtimes)

    def start(self) -> None:
        for runtime in self._runtimes:
            runtime.start()

    def stop(self) -> None:
        for runtime in self._runtimes:
            runtime.stop()

    def latest_for_event(self, event_ts: str | None, time_window_ms: int) -> dict[str, Any] | None:
        if time_window_ms <= 0:
            return None
        event_dt = _parse_ts(event_ts) or _utc_now()
        window = timedelta(milliseconds=time_window_ms)
        nearest_payload: dict[str, Any] | None = None
        nearest_delta: timedelta | None = None

        for runtime in self._runtimes:
            payload = runtime.latest_for_event(event_ts, time_window_ms)
            if payload is None:
                continue
            payload_dt = _parse_ts(
                payload.get("sensor_ts")
                or payload.get("source_ts")
                or payload.get("ts")
                or payload.get("ingest_ts"),
            ) or event_dt
            delta = abs(payload_dt - event_dt)
            if delta > window:
                continue
            if nearest_payload is None or nearest_delta is None or delta < nearest_delta:
                nearest_payload = payload
                nearest_delta = delta
        return dict(nearest_payload) if nearest_payload is not None else None

    def drain_packets(self, limit: int | None = None) -> list[SensorPacket]:
        packets: list[SensorPacket] = []
        for runtime in self._runtimes:
            packets.extend(runtime.drain_packets())
        if not packets:
            return []
        packets.sort(key=lambda item: item.event_ts)
        if limit is None or limit <= 0:
            return packets
        return packets[:limit]

    def last_packet_ts(self) -> datetime | None:
        latest: datetime | None = None
        for runtime in self._runtimes:
            ts = runtime.last_packet_ts()
            if ts is None:
                continue
            if latest is None or ts > latest:
                latest = ts
        return latest

    def last_packet_age_sec(self) -> float | None:
        ts = self.last_packet_ts()
        if ts is None:
            return None
        age = (_utc_now() - ts).total_seconds()
        return round(max(0.0, age), 3)
