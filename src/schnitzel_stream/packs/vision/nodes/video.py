from __future__ import annotations

"""
Video nodes (OpenCV).

Intent:
- Provide a minimal file-video source for v2 graphs (Phase 4 parity work).
- Keep OpenCV optional at import time: edges without cv2 can still import the package.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.project import resolve_project_root
from schnitzel_stream.utils.urls import mask_url

try:  # pragma: no cover
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


def _parse_iso_dt(s: str) -> datetime:
    raw = str(s or "").strip()
    if not raw:
        raise ValueError("empty timestamp")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        # Treat naive inputs as UTC to avoid silent localtime behavior.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class OpenCvVideoFileSource:
    """Read frames from a video file and emit `kind=frame` packets.

    Output payload:
    - frame: np.ndarray (BGR)  (in-proc only; non-portable)
    - frame_idx: int

    Config:
    - path: str (required)
    - source_id: str (default: node_id)
    - max_frames: int (default: 0 -> no limit)
    - start_ts: str (optional ISO-8601)
      - If provided, packet.ts is computed as start_ts + video_pos_msec.
      - If omitted, packet.ts is generated at emit-time (not deterministic across runs).
    """

    OUTPUT_KINDS = {"frame"}

    node_id: str
    path: str
    source_id: str
    max_frames: int
    start_ts: datetime | None

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        if cv2 is None:
            raise ImportError("OpenCvVideoFileSource requires opencv-python(-headless)")

        cfg = dict(config or {})
        path = cfg.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("OpenCvVideoFileSource requires config.path (video file path)")
        p = Path(path.strip())
        if not p.is_absolute():
            # Intent: keep relative paths stable regardless of CWD (edge devices + subprocess runs).
            p = resolve_project_root() / p
        if not p.exists():
            raise FileNotFoundError(f"video file not found: {p}")

        self.node_id = str(node_id or "video_file")
        self.path = str(p)
        self.source_id = str(cfg.get("source_id") or self.node_id)

        max_frames = int(cfg.get("max_frames", 0))
        if max_frames < 0:
            raise ValueError("OpenCvVideoFileSource config.max_frames must be >= 0")
        self.max_frames = max_frames

        start_ts_raw = cfg.get("start_ts")
        self.start_ts = _parse_iso_dt(start_ts_raw) if isinstance(start_ts_raw, str) and start_ts_raw.strip() else None

        # Intent: keep the capture as instance state so runtime throttles can stop early
        # without leaking file handles (runner always calls node.close()).
        self._cap = cv2.VideoCapture(self.path)
        if not self._cap.isOpened():
            raise RuntimeError(f"failed to open video file: {self.path}")
        self._closed = False

    def run(self) -> Iterable[StreamPacket]:
        assert cv2 is not None  # for type checkers
        if self._closed:
            return []

        frame_idx = 0
        while True:
            ok, frame = self._cap.read()
            if not ok:
                break

            pos_msec = float(self._cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
            if self.start_ts is not None:
                ts = (self.start_ts + timedelta(milliseconds=pos_msec)).isoformat()
            else:
                # Intent: without an explicit clock anchor, file playback timestamps
                # are not stable across re-runs; use wall clock for now.
                ts = datetime.now(timezone.utc).isoformat()

            meta = {
                "frame_idx": int(frame_idx),
                "pos_msec": int(pos_msec),
                # Intent: deterministic frame id for at-least-once replay within a stream.
                "idempotency_key": f"frame:{self.source_id}:{frame_idx}",
            }

            payload = {"frame": frame, "frame_idx": int(frame_idx)}
            yield StreamPacket.new(kind="frame", source_id=self.source_id, payload=payload, ts=ts, meta=meta)

            frame_idx += 1
            if self.max_frames and frame_idx >= self.max_frames:
                break

    def close(self) -> None:
        if getattr(self, "_closed", True):
            return
        self._closed = True
        cap = getattr(self, "_cap", None)
        if cap is not None:
            cap.release()


@dataclass
class OpenCvRtspSource:
    """Read frames from an RTSP URL and emit `kind=frame` packets.

    Output payload:
    - frame: np.ndarray (BGR)  (in-proc only; non-portable)
    - frame_idx: int

    Config:
    - url: str (required)
    - source_id: str (default: node_id)
    - max_frames: int (default: 0 -> no limit; combine with CLI `--max-events` for demos)
    - reconnect: bool (default: true)
    - reconnect_backoff_sec: float (default: 1.0)
    - reconnect_backoff_max_sec: float (default: 30.0)
    - reconnect_max_attempts: int (default: 0 -> unlimited)
    """

    OUTPUT_KINDS = {"frame"}

    node_id: str
    url: str
    source_id: str
    max_frames: int
    reconnect: bool
    reconnect_backoff_sec: float
    reconnect_backoff_max_sec: float
    reconnect_max_attempts: int

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        if cv2 is None:
            raise ImportError("OpenCvRtspSource requires opencv-python(-headless)")

        cfg = dict(config or {})
        url = cfg.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("OpenCvRtspSource requires config.url (rtsp url)")

        self.node_id = str(node_id or "rtsp")
        self.url = str(url.strip())
        self.source_id = str(cfg.get("source_id") or self.node_id)

        max_frames = int(cfg.get("max_frames", 0))
        if max_frames < 0:
            raise ValueError("OpenCvRtspSource config.max_frames must be >= 0")
        self.max_frames = max_frames

        self.reconnect = bool(cfg.get("reconnect", True))
        self.reconnect_backoff_sec = float(cfg.get("reconnect_backoff_sec", 1.0))
        self.reconnect_backoff_max_sec = float(cfg.get("reconnect_backoff_max_sec", 30.0))
        self.reconnect_max_attempts = int(cfg.get("reconnect_max_attempts", 0))

        self._cap = None
        self._closed = False
        self._epoch = 0
        self._open_capture_or_raise()

    def _open_capture(self) -> Any:
        assert cv2 is not None  # for type checkers
        cap = cv2.VideoCapture(self.url)
        if not cap.isOpened():
            try:
                cap.release()
            finally:
                return None
        return cap

    def _open_capture_or_raise(self) -> None:
        if self._closed:
            return

        attempts = 0
        backoff = max(0.0, float(self.reconnect_backoff_sec))
        backoff_max = max(backoff, float(self.reconnect_backoff_max_sec))

        while not self._closed:
            cap = self._open_capture()
            if cap is not None:
                self._cap = cap
                self._epoch += 1
                return

            attempts += 1
            if not self.reconnect:
                raise RuntimeError(f"failed to open RTSP stream: {mask_url(self.url)}")
            if self.reconnect_max_attempts > 0 and attempts >= self.reconnect_max_attempts:
                raise RuntimeError(
                    f"failed to open RTSP stream after {attempts} attempts: {mask_url(self.url)}",
                )
            if backoff > 0:
                time.sleep(backoff)
            backoff = min(backoff_max, backoff * 2.0 if backoff > 0 else 0.0)

    def run(self) -> Iterable[StreamPacket]:
        assert cv2 is not None  # for type checkers
        if self._closed:
            return []

        frame_idx = 0
        while not self._closed:
            cap = getattr(self, "_cap", None)
            if cap is None:
                break

            ok, frame = cap.read()
            if not ok:
                if not self.reconnect:
                    break
                try:
                    cap.release()
                finally:
                    self._cap = None
                self._open_capture_or_raise()
                continue

            ts = datetime.now(timezone.utc).isoformat()
            meta = {
                "frame_idx": int(frame_idx),
                "epoch": int(self._epoch),
                "idempotency_key": f"frame:{self.source_id}:{self._epoch}:{frame_idx}",
            }
            payload = {"frame": frame, "frame_idx": int(frame_idx)}
            yield StreamPacket.new(kind="frame", source_id=self.source_id, payload=payload, ts=ts, meta=meta)

            frame_idx += 1
            if self.max_frames and frame_idx >= self.max_frames:
                break

    def close(self) -> None:
        if getattr(self, "_closed", True):
            return
        self._closed = True
        cap = getattr(self, "_cap", None)
        if cap is not None:
            cap.release()


@dataclass
class EveryNthFrameSamplerNode:
    """Drop frames except every Nth packet.

    Config:
    - every_n: int (default: 1)
    - offset: int (default: 0) : accept if (frame_idx - offset) % every_n == 0
    """

    INPUT_KINDS = {"frame"}
    OUTPUT_KINDS = {"frame"}

    node_id: str
    every_n: int
    offset: int
    kept_total: int = 0
    dropped_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self.node_id = str(node_id or "every_n_sampler")
        self.every_n = max(1, int(cfg.get("every_n", 1)))
        self.offset = int(cfg.get("offset", 0))
        self.kept_total = 0
        self.dropped_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self.node_id}: expected frame payload as a mapping")
        frame_idx = packet.payload.get("frame_idx")
        if not isinstance(frame_idx, int):
            raise TypeError(f"{self.node_id}: expected payload.frame_idx as int")

        if ((frame_idx - self.offset) % self.every_n) == 0:
            self.kept_total += 1
            return [packet]

        self.dropped_total += 1
        return []

    def metrics(self) -> dict[str, int]:
        return {"kept_total": int(self.kept_total), "dropped_total": int(self.dropped_total)}

    def close(self) -> None:
        return
