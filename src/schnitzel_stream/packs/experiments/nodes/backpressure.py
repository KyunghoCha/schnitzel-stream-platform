from __future__ import annotations

"""
Backpressure fairness experiment nodes.

Intent:
- Provide deterministic synthetic workloads for repeatable policy comparisons.
- Capture per-packet timing/metadata without changing core runtime contracts.
"""

from dataclasses import dataclass, replace
import json
from pathlib import Path
import random
import time
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket


def _as_int(raw: Any, *, default: int, minimum: int | None = None) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = int(default)
    if minimum is not None and value < int(minimum):
        return int(minimum)
    return int(value)


def _as_float(raw: Any, *, default: float, minimum: float | None = None) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = float(default)
    if minimum is not None and value < float(minimum):
        return float(minimum)
    return float(value)


def _as_dict(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _as_list(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return list(raw)
    return []


def _group_probabilities(*, groups: list[str], probs_raw: dict[str, Any]) -> list[tuple[str, float]]:
    if not groups:
        groups = ["group_a", "group_b"]
    probs: list[tuple[str, float]] = []
    total = 0.0
    for g in groups:
        p = _as_float(probs_raw.get(g), default=0.0, minimum=0.0)
        probs.append((g, p))
        total += p
    if total <= 0.0:
        uniform = 1.0 / float(len(groups))
        return [(g, uniform) for g in groups]
    return [(g, p / total) for g, p in probs]


def _sample_group(rng: random.Random, probs: list[tuple[str, float]]) -> str:
    if not probs:
        return "group_a"
    cut = rng.random()
    acc = 0.0
    for group_id, p in probs:
        acc += p
        if cut <= acc:
            return group_id
    return probs[-1][0]


@dataclass(frozen=True)
class PlannedEvent:
    seq: int
    group_id: str
    logical_ts_ms: float
    recovery_marker: bool


def generate_event_plan(config: dict[str, Any], *, seed: int) -> list[PlannedEvent]:
    cfg = dict(config or {})
    total_events = _as_int(cfg.get("total_events"), default=600, minimum=0)
    event_interval_ms = _as_float(cfg.get("event_interval_ms"), default=10.0, minimum=0.0)
    burst_every = _as_int(cfg.get("burst_every"), default=0, minimum=0)
    burst_size = _as_int(cfg.get("burst_size"), default=1, minimum=1)
    recovery_marker_seq = _as_int(cfg.get("recovery_marker_seq"), default=-1)

    groups_raw = _as_list(cfg.get("groups"))
    groups = [str(x).strip() for x in groups_raw if str(x).strip()]
    probs = _group_probabilities(groups=groups, probs_raw=_as_dict(cfg.get("group_probs")))

    rng = random.Random(int(seed))
    out: list[PlannedEvent] = []
    seq = 0
    logical_ts_ms = 0.0

    for base_idx in range(total_events):
        copies = burst_size if burst_every > 0 and (base_idx % burst_every) == 0 else 1
        for _ in range(copies):
            out.append(
                PlannedEvent(
                    seq=int(seq),
                    group_id=_sample_group(rng, probs),
                    logical_ts_ms=float(logical_ts_ms),
                    recovery_marker=seq == recovery_marker_seq,
                )
            )
            seq += 1
        logical_ts_ms += event_interval_ms
    return out


class SyntheticRiskEventSource:
    """Deterministic source for fairness/backpressure workloads."""

    OUTPUT_KINDS = {"event"}
    OUTPUT_PROFILE = "json_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "synthetic_source")
        self._source_id = str(cfg.get("source_id", "synthetic_source")).strip() or "synthetic_source"
        self._seed = _as_int(cfg.get("seed"), default=0)
        self._outage_sleep_ms = _as_float(cfg.get("outage_sleep_ms"), default=0.0, minimum=0.0)
        self._emit_sleep_ms = _as_float(cfg.get("emit_sleep_ms"), default=0.0, minimum=0.0)
        self._signal_scale = _as_float(cfg.get("signal_scale"), default=1.0, minimum=0.0)
        self._cfg = cfg
        self._plan = generate_event_plan(cfg, seed=self._seed)
        self._emitted_total = 0

    def run(self) -> Iterable[StreamPacket]:
        for item in self._plan:
            if item.recovery_marker and self._outage_sleep_ms > 0.0:
                time.sleep(self._outage_sleep_ms / 1000.0)

            emitted_ns = time.monotonic_ns()
            payload = {
                "event_id": f"{self._source_id}:{item.seq:08d}",
                "seq": int(item.seq),
                "group_id": str(item.group_id),
                "logical_ts_ms": float(item.logical_ts_ms),
                "signal": float((item.seq % 10) / 10.0) * float(self._signal_scale),
            }
            meta = {
                "seq": int(item.seq),
                "group_id": str(item.group_id),
                "recovery_marker": bool(item.recovery_marker),
                "emitted_mono_ns": int(emitted_ns),
                "expected_total": int(len(self._plan)),
            }
            self._emitted_total += 1
            yield StreamPacket.new(kind="event", source_id=self._source_id, payload=payload, meta=meta)

            if self._emit_sleep_ms > 0.0:
                time.sleep(self._emit_sleep_ms / 1000.0)

    def metrics(self) -> dict[str, int]:
        return {
            "emitted_total": int(self._emitted_total),
            "expected_total": int(len(self._plan)),
        }

    def close(self) -> None:
        return


class SlowScoringNode:
    """Inject controlled delay and attach score fields."""

    INPUT_KINDS = {"event"}
    OUTPUT_KINDS = {"event"}
    INPUT_PROFILE = "json_portable"
    OUTPUT_PROFILE = "json_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "slow_scoring")
        self._delay_ms = _as_float(cfg.get("delay_ms"), default=1.5, minimum=0.0)
        self._jitter_ms = _as_float(cfg.get("jitter_ms"), default=0.0, minimum=0.0)
        self._seed = _as_int(cfg.get("seed"), default=0)
        self._group_delay_ms = {
            str(k): _as_float(v, default=0.0, minimum=0.0) for k, v in _as_dict(cfg.get("group_delay_ms")).items()
        }
        self._rng = random.Random(self._seed)
        self._processed_total = 0

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, dict):
            raise TypeError(f"{self._node_id}: expected packet.payload as mapping")
        payload = dict(packet.payload)
        group_id = str(payload.get("group_id", packet.meta.get("group_id", "group_a")))

        delay_ms = self._delay_ms + float(self._group_delay_ms.get(group_id, 0.0))
        if self._jitter_ms > 0.0:
            delay_ms += self._rng.uniform(-self._jitter_ms, self._jitter_ms)
        if delay_ms > 0.0:
            time.sleep(delay_ms / 1000.0)

        signal = _as_float(payload.get("signal"), default=0.0)
        seq = _as_int(payload.get("seq"), default=0)
        payload["risk_score"] = round(signal * 0.75 + (seq % 5) * 0.05, 6)
        payload["policy_group"] = group_id

        meta = dict(packet.meta)
        meta["processed_mono_ns"] = int(time.monotonic_ns())
        self._processed_total += 1
        return [replace(packet, payload=payload, meta=meta)]

    def metrics(self) -> dict[str, int]:
        return {"processed_total": int(self._processed_total)}

    def close(self) -> None:
        return


class BackpressureMetricsSink:
    """Write one JSON line per observed packet for offline analysis."""

    INPUT_KINDS = {"event"}
    OUTPUT_KINDS = {"event"}
    INPUT_PROFILE = "json_portable"
    OUTPUT_PROFILE = "json_portable"

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._node_id = str(node_id or "metrics_sink")

        output_path = str(cfg.get("output_path", "")).strip()
        if not output_path:
            raise ValueError("BackpressureMetricsSink requires config.output_path")
        self._path = Path(output_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("w", encoding="utf-8")

        self._flush = bool(cfg.get("flush", True))
        self._forward = bool(cfg.get("forward", False))
        self._write_total = 0
        self._write_error_total = 0
        self._recovery_marker_seen_total = 0

    @property
    def path(self) -> Path:
        return self._path

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        now_ns = time.monotonic_ns()
        payload = dict(packet.payload) if isinstance(packet.payload, dict) else {}
        meta = dict(packet.meta)

        seq = _as_int(payload.get("seq", meta.get("seq", -1)), default=-1)
        group_id = str(payload.get("group_id", meta.get("group_id", "unknown")))
        emitted_ns = _as_int(meta.get("emitted_mono_ns"), default=0, minimum=0)
        latency_ms = ((now_ns - emitted_ns) / 1_000_000.0) if emitted_ns > 0 else None
        marker = bool(meta.get("recovery_marker", False))
        if marker:
            self._recovery_marker_seen_total += 1

        rec = {
            "node_id": self._node_id,
            "packet_id": str(packet.packet_id),
            "seq": int(seq),
            "group_id": group_id,
            "source_id": str(packet.source_id),
            "kind": str(packet.kind),
            "logical_ts_ms": _as_float(payload.get("logical_ts_ms"), default=0.0, minimum=0.0),
            "latency_ms": None if latency_ms is None else float(latency_ms),
            "observed_mono_ns": int(now_ns),
            "emitted_mono_ns": int(emitted_ns),
            "recovery_marker": marker,
        }
        try:
            self._fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if self._flush:
                self._fh.flush()
            self._write_total += 1
        except OSError:
            self._write_error_total += 1
            raise

        if self._forward:
            return [packet]
        return []

    def metrics(self) -> dict[str, int]:
        return {
            "written_total": int(self._write_total),
            "write_error_total": int(self._write_error_total),
            "recovery_marker_seen_total": int(self._recovery_marker_seen_total),
        }

    def close(self) -> None:
        fh = getattr(self, "_fh", None)
        if fh is not None:
            fh.close()

