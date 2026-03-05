#!/usr/bin/env python3
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from schnitzel_stream.packs.experiments.nodes.backpressure import generate_event_plan


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_path(*, project_root: Path, raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (project_root / p).resolve()


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(dict(out[key]), dict(value))
        else:
            out[key] = copy.deepcopy(value)
    return out


def as_dict(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def as_list(raw: Any) -> list[Any]:
    return list(raw) if isinstance(raw, list) else []


def as_int(raw: Any, *, default: int, minimum: int | None = None) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = int(default)
    if minimum is not None and value < int(minimum):
        return int(minimum)
    return int(value)


def as_float(raw: Any, *, default: float, minimum: float | None = None) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = float(default)
    if minimum is not None and value < float(minimum):
        return float(minimum)
    return float(value)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    qn = min(1.0, max(0.0, float(q)))
    arr = sorted(values)
    idx = (len(arr) - 1) * qn
    low = int(math.floor(idx))
    high = int(math.ceil(idx))
    if low == high:
        return float(arr[low])
    weight = idx - low
    return float(arr[low] * (1.0 - weight) + arr[high] * weight)


def mode_str(values: list[str], *, default: str = "") -> str:
    if not values:
        return str(default)
    counts: dict[str, int] = {}
    for item in values:
        key = str(item)
        counts[key] = int(counts.get(key, 0)) + 1
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return best[0][0] if best else str(default)


def discover(*, project_root: Path, pattern: str) -> list[Path]:
    matches = sorted(project_root.glob(pattern))
    return [p.resolve() for p in matches if p.is_file()]


def require_string(value: Any, *, name: str) -> str:
    txt = str(value or "").strip()
    if not txt:
        raise ValueError(f"{name} must be non-empty")
    return txt


def patch_node_config(graph: dict[str, Any], *, node_id: str, patch: dict[str, Any]) -> None:
    for item in as_list(graph.get("nodes")):
        row = as_dict(item)
        current_id = str(row.get("id", row.get("node_id", ""))).strip()
        if current_id != node_id:
            continue
        merged = deep_merge(as_dict(row.get("config")), patch)
        row["config"] = merged
        if "id" in row:
            row["id"] = current_id
        else:
            row["node_id"] = current_id
        item.clear()
        item.update(row)
        return
    raise ValueError(f"node not found in graph: {node_id}")


def node_config(graph: dict[str, Any], *, node_id: str) -> dict[str, Any]:
    for item in as_list(graph.get("nodes")):
        row = as_dict(item)
        current_id = str(row.get("id", row.get("node_id", ""))).strip()
        if current_id == node_id:
            return as_dict(row.get("config"))
    raise ValueError(f"node not found in graph: {node_id}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        txt = line.strip()
        if not txt:
            continue
        try:
            obj = json.loads(txt)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def expected_counts(*, source_cfg: dict[str, Any], burst_cfg: dict[str, Any], seed: int) -> tuple[int, dict[str, int]]:
    source_plan = generate_event_plan(source_cfg, seed=int(seed))
    burst_count = as_int(burst_cfg.get("count"), default=1, minimum=1)
    expected_total = int(len(source_plan) * burst_count)
    expected_by_group: dict[str, int] = {}
    for item in source_plan:
        g = str(getattr(item, "group_id", "unknown"))
        expected_by_group[g] = int(expected_by_group.get(g, 0)) + burst_count
    return expected_total, expected_by_group


def metrics_from_run(
    *,
    records: list[dict[str, Any]],
    expected_total: int,
    expected_by_group: dict[str, int],
    duration_sec: float,
    runtime_metrics: dict[str, int],
    group_weights: dict[str, float],
    latency_budget_ms: float,
    status: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected_total = int(expected_total)
    observed_total = int(len(records))
    runtime_drop_total = int(runtime_metrics.get("packets.dropped_total", 0))
    missed_total = max(0, expected_total - observed_total)

    latencies = [
        float(r["latency_ms"]) for r in records if isinstance(r.get("latency_ms"), (int, float)) and r["latency_ms"] >= 0.0
    ]
    throughput = float(observed_total / duration_sec) if duration_sec > 0 else 0.0

    expected_by_group = {str(k): int(v) for k, v in expected_by_group.items()}

    observed_by_group: dict[str, int] = {}
    latencies_by_group: dict[str, list[float]] = {}
    recovery_latencies: list[float] = []
    for row in records:
        g = str(row.get("group_id", "unknown"))
        observed_by_group[g] = int(observed_by_group.get(g, 0)) + 1
        latency = row.get("latency_ms")
        if isinstance(latency, (int, float)) and latency >= 0.0:
            latencies_by_group.setdefault(g, []).append(float(latency))
            if bool(row.get("recovery_marker", False)):
                recovery_latencies.append(float(latency))

    all_groups = sorted(set(expected_by_group) | set(observed_by_group))
    group_miss_rate_map: dict[str, float] = {}
    group_latency_p95_map: dict[str, float | None] = {}
    worst_group_id = ""
    worst_group_rank = (-1.0, -1.0, "")
    for g in all_groups:
        exp = int(expected_by_group.get(g, 0))
        obs = int(observed_by_group.get(g, 0))
        miss = max(0, exp - obs)
        miss_rate = float(miss / exp) if exp > 0 else 0.0
        p95 = percentile(latencies_by_group.get(g, []), 0.95) if latencies_by_group.get(g) else None
        group_miss_rate_map[g] = float(miss_rate)
        group_latency_p95_map[g] = None if p95 is None else float(p95)

        p95_rank = float(p95) if p95 is not None else 1_000_000.0
        rank = (float(miss_rate), p95_rank, g)
        if rank > worst_group_rank:
            worst_group_rank = rank
            worst_group_id = g

    miss_rates = list(group_miss_rate_map.values())
    p95_values = [float(v) for v in group_latency_p95_map.values() if isinstance(v, (int, float))]
    group_miss_gap = (max(miss_rates) - min(miss_rates)) if miss_rates else 0.0
    group_latency_gap_ms = (max(p95_values) - min(p95_values)) if p95_values else 0.0

    weights: dict[str, float] = {}
    for g in all_groups:
        raw = group_weights.get(g, 1.0)
        w = float(raw) if isinstance(raw, (int, float)) else 1.0
        weights[g] = max(0.0, w)
    weight_sum = float(sum(weights.values())) if weights else 0.0
    if weight_sum <= 0.0:
        weight_sum = float(len(all_groups)) if all_groups else 1.0
        weights = {g: 1.0 for g in all_groups}

    weighted_miss = 0.0
    weighted_latency_ratio = 0.0
    for g in all_groups:
        w = float(weights.get(g, 1.0))
        weighted_miss += w * float(group_miss_rate_map.get(g, 0.0))
        p95 = group_latency_p95_map.get(g)
        p95_val = float(p95) if isinstance(p95, (int, float)) else float(latency_budget_ms * 5.0)
        weighted_latency_ratio += w * min(5.0, p95_val / max(1.0, latency_budget_ms))
    weighted_miss /= weight_sum
    weighted_latency_ratio /= weight_sum

    error_penalty = 5.0 if status != "ok" else 0.0
    harm_weighted_cost = weighted_miss * 100.0 + weighted_latency_ratio * 10.0 + error_penalty

    metrics = {
        "expected_total": int(expected_total),
        "observed_total": int(observed_total),
        "missed_total": int(missed_total),
        "drop_total_runtime": int(runtime_drop_total),
        "throughput": float(throughput),
        "p50_latency_ms": float(percentile(latencies, 0.50)) if latencies else 0.0,
        "p95_latency_ms": float(percentile(latencies, 0.95)) if latencies else 0.0,
        "p99_latency_ms": float(percentile(latencies, 0.99)) if latencies else 0.0,
        "drop_rate": float(runtime_drop_total / expected_total) if expected_total > 0 else 0.0,
        "event_miss_rate": float(missed_total / expected_total) if expected_total > 0 else 0.0,
        "recovery_time_ms": float(recovery_latencies[0]) if recovery_latencies else None,
        "group_miss_gap": float(group_miss_gap),
        "group_latency_gap_ms": float(group_latency_gap_ms),
        "weighted_miss_rate": float(weighted_miss),
        "weighted_latency_ratio": float(weighted_latency_ratio),
        "harm_weighted_cost": float(harm_weighted_cost),
        "worst_group_id": str(worst_group_id),
        "worst_group_miss_rate": float(group_miss_rate_map.get(worst_group_id, 0.0)),
        "worst_group_latency_p95_ms": (
            None
            if worst_group_id not in group_latency_p95_map or group_latency_p95_map[worst_group_id] is None
            else float(group_latency_p95_map[worst_group_id])  # type: ignore[arg-type]
        ),
    }
    breakdown = {
        "expected_by_group": expected_by_group,
        "observed_by_group": observed_by_group,
        "group_miss_rate": group_miss_rate_map,
        "group_latency_p95_ms": group_latency_p95_map,
        "group_weights": weights,
    }
    return metrics, breakdown
