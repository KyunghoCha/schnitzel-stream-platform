#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time
from typing import Any

from omegaconf import OmegaConf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.packs.experiments.nodes.backpressure import generate_event_plan
from schnitzel_stream.runtime.inproc import InProcGraphRunner


SCHEMA_VERSION = 1
DEFAULT_BASE = "configs/experiments/backpressure_fairness/bench_base.yaml"
DEFAULT_POLICY_GLOB = "configs/experiments/backpressure_fairness/policy_*.yaml"
DEFAULT_WORKLOAD_GLOB = "configs/experiments/backpressure_fairness/workloads_*.yaml"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_path(raw: str) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = OmegaConf.load(path)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"yaml must be a mapping: {path}")
    return dict(cont)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(dict(out[key]), dict(value))
        else:
            out[key] = copy.deepcopy(value)
    return out


def _as_dict(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _as_list(raw: Any) -> list[Any]:
    return list(raw) if isinstance(raw, list) else []


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


def _percentile(values: list[float], q: float) -> float:
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


def _mode_str(values: list[str], *, default: str = "") -> str:
    if not values:
        return str(default)
    counts: dict[str, int] = {}
    for item in values:
        key = str(item)
        counts[key] = int(counts.get(key, 0)) + 1
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return best[0][0] if best else str(default)


def _discover(pattern: str) -> list[Path]:
    matches = sorted(PROJECT_ROOT.glob(pattern))
    return [p.resolve() for p in matches if p.is_file()]


def _require_string(value: Any, *, name: str) -> str:
    txt = str(value or "").strip()
    if not txt:
        raise ValueError(f"{name} must be non-empty")
    return txt


def _build_specs(graph: dict[str, Any]) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    nodes: list[NodeSpec] = []
    edges: list[EdgeSpec] = []

    for idx, item in enumerate(_as_list(graph.get("nodes"))):
        row = _as_dict(item)
        node_id = _require_string(row.get("id", row.get("node_id")), name=f"graph.nodes[{idx}].id")
        plugin = _require_string(row.get("plugin"), name=f"graph.nodes[{idx}].plugin")
        kind = _require_string(row.get("kind", "node"), name=f"graph.nodes[{idx}].kind")
        config = _as_dict(row.get("config"))
        nodes.append(NodeSpec(node_id=node_id, plugin=plugin, kind=kind, config=config))

    for idx, item in enumerate(_as_list(graph.get("edges"))):
        row = _as_dict(item)
        src = _require_string(row.get("from", row.get("src")), name=f"graph.edges[{idx}].from")
        dst = _require_string(row.get("to", row.get("dst")), name=f"graph.edges[{idx}].to")
        src_port = row.get("from_port", row.get("src_port"))
        dst_port = row.get("to_port", row.get("dst_port"))
        src_port_val = str(src_port).strip() if isinstance(src_port, str) and src_port.strip() else None
        dst_port_val = str(dst_port).strip() if isinstance(dst_port, str) and dst_port.strip() else None
        edges.append(EdgeSpec(src=src, dst=dst, src_port=src_port_val, dst_port=dst_port_val))
    return nodes, edges


def _patch_node_config(graph: dict[str, Any], *, node_id: str, patch: dict[str, Any]) -> None:
    for item in _as_list(graph.get("nodes")):
        row = _as_dict(item)
        current_id = str(row.get("id", row.get("node_id", ""))).strip()
        if current_id != node_id:
            continue
        merged = _deep_merge(_as_dict(row.get("config")), patch)
        row["config"] = merged
        if "id" in row:
            row["id"] = current_id
        else:
            row["node_id"] = current_id
        item.clear()
        item.update(row)
        return
    raise ValueError(f"node not found in graph: {node_id}")


def _node_config(graph: dict[str, Any], *, node_id: str) -> dict[str, Any]:
    for item in _as_list(graph.get("nodes")):
        row = _as_dict(item)
        current_id = str(row.get("id", row.get("node_id", ""))).strip()
        if current_id == node_id:
            return _as_dict(row.get("config"))
    raise ValueError(f"node not found in graph: {node_id}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def _expected_counts(*, source_cfg: dict[str, Any], burst_cfg: dict[str, Any], seed: int) -> tuple[int, dict[str, int]]:
    source_plan = generate_event_plan(source_cfg, seed=int(seed))
    burst_count = _as_int(burst_cfg.get("count"), default=1, minimum=1)
    expected_total = int(len(source_plan) * burst_count)
    expected_by_group: dict[str, int] = {}
    for item in source_plan:
        g = str(getattr(item, "group_id", "unknown"))
        expected_by_group[g] = int(expected_by_group.get(g, 0)) + burst_count
    return expected_total, expected_by_group


def _metrics_from_run(
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
        p95 = _percentile(latencies_by_group.get(g, []), 0.95) if latencies_by_group.get(g) else None
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
        "p50_latency_ms": float(_percentile(latencies, 0.50)) if latencies else 0.0,
        "p95_latency_ms": float(_percentile(latencies, 0.95)) if latencies else 0.0,
        "p99_latency_ms": float(_percentile(latencies, 0.99)) if latencies else 0.0,
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


def _run_once(
    *,
    base_cfg: dict[str, Any],
    policy_cfg: dict[str, Any],
    workload_cfg: dict[str, Any],
    repeat: int,
    seed: int,
    session_dir: Path,
    run_id: str,
) -> dict[str, Any]:
    graph = copy.deepcopy(_as_dict(base_cfg.get("graph")))
    node_ids = _deep_merge(
        {
            "source": "src",
            "burst": "burst",
            "processor": "processor",
            "sink": "sink",
        },
        _as_dict(base_cfg.get("node_ids")),
    )
    source_node_id = str(node_ids["source"])
    burst_node_id = str(node_ids["burst"])
    processor_node_id = str(node_ids["processor"])
    sink_node_id = str(node_ids["sink"])

    for node_id, patch in _as_dict(workload_cfg.get("node_overrides")).items():
        _patch_node_config(graph, node_id=str(node_id), patch=_as_dict(patch))
    for node_id, patch in _as_dict(policy_cfg.get("node_overrides")).items():
        _patch_node_config(graph, node_id=str(node_id), patch=_as_dict(patch))

    source_patch = _as_dict(workload_cfg.get("source_config"))
    burst_patch = _as_dict(workload_cfg.get("burst_config"))
    processor_patch = _as_dict(workload_cfg.get("processor_config"))
    sink_patch = _as_dict(workload_cfg.get("sink_config"))
    if source_patch:
        _patch_node_config(graph, node_id=source_node_id, patch=source_patch)
    if burst_patch:
        _patch_node_config(graph, node_id=burst_node_id, patch=burst_patch)
    if processor_patch:
        _patch_node_config(graph, node_id=processor_node_id, patch=processor_patch)
    if sink_patch:
        _patch_node_config(graph, node_id=sink_node_id, patch=sink_patch)

    _patch_node_config(graph, node_id=source_node_id, patch={"seed": int(seed)})
    _patch_node_config(graph, node_id=processor_node_id, patch={"seed": int(seed + 977)})

    events_dir = session_dir / "events"
    runs_dir = session_dir / "runs"
    events_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    events_path = events_dir / f"{run_id}.jsonl"
    _patch_node_config(graph, node_id=sink_node_id, patch={"output_path": str(events_path)})

    nodes, edges = _build_specs(graph)

    policy_id = str(policy_cfg.get("policy_id", "unknown"))
    workload_id = str(workload_cfg.get("workload_id", "unknown"))
    latency_budget_ms = _as_float(
        workload_cfg.get("latency_budget_ms", base_cfg.get("latency_budget_ms", 100.0)),
        default=100.0,
        minimum=1.0,
    )

    source_cfg = _node_config(graph, node_id=source_node_id)
    burst_cfg = _node_config(graph, node_id=burst_node_id)
    sink_cfg = _node_config(graph, node_id=sink_node_id)
    expected_total, expected_by_group = _expected_counts(source_cfg=source_cfg, burst_cfg=burst_cfg, seed=int(seed))
    group_weights = {
        str(k): float(v)
        for k, v in _as_dict(sink_cfg.get("group_weights")).items()
        if isinstance(v, (int, float))
    }

    started_ns = time.monotonic_ns()
    status = "ok"
    err = ""
    runtime_metrics: dict[str, int] = {}
    try:
        runner = InProcGraphRunner()
        result = runner.run(nodes=nodes, edges=edges)
        runtime_metrics = dict(result.metrics)
    except Exception as exc:
        status = "error"
        err = f"{type(exc).__name__}: {exc}"
    duration_sec = float((time.monotonic_ns() - started_ns) / 1_000_000_000.0)

    records = _read_jsonl(events_path)
    metrics, breakdown = _metrics_from_run(
        records=records,
        expected_total=expected_total,
        expected_by_group=expected_by_group,
        duration_sec=duration_sec,
        runtime_metrics=runtime_metrics,
        group_weights=group_weights,
        latency_budget_ms=latency_budget_ms,
        status=status,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "status": status,
        "error": err,
        "experiment_id": str(base_cfg.get("experiment_id", "backpressure_fairness")),
        "policy": policy_id,
        "policy_id": policy_id,
        "workload_id": workload_id,
        "seed": int(seed),
        "repeat": int(repeat),
        "run_id": run_id,
        "duration_sec": float(duration_sec),
        "throughput": float(metrics["throughput"]),
        "p50_latency_ms": float(metrics["p50_latency_ms"]),
        "p95_latency_ms": float(metrics["p95_latency_ms"]),
        "p99_latency_ms": float(metrics["p99_latency_ms"]),
        "drop_rate": float(metrics["drop_rate"]),
        "event_miss_rate": float(metrics["event_miss_rate"]),
        "recovery_time_ms": metrics["recovery_time_ms"],
        "group_id": str(metrics["worst_group_id"]),
        "group_miss_rate": float(metrics["worst_group_miss_rate"]),
        "group_latency_p95_ms": metrics["worst_group_latency_p95_ms"],
        "group_miss_gap": float(metrics["group_miss_gap"]),
        "group_latency_gap_ms": float(metrics["group_latency_gap_ms"]),
        "weighted_miss_rate": float(metrics["weighted_miss_rate"]),
        "weighted_latency_ratio": float(metrics["weighted_latency_ratio"]),
        "harm_weighted_cost": float(metrics["harm_weighted_cost"]),
        "metrics": metrics,
        "group_metrics": breakdown,
        "runtime_metrics": runtime_metrics,
        "paths": {
            "events_path": str(events_path),
        },
    }
    out_path = runs_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["paths"]["run_path"] = str(out_path)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run backpressure fairness benchmark workloads")
    parser.add_argument("--base", default=DEFAULT_BASE, help="base benchmark yaml")
    parser.add_argument("--policy", action="append", default=[], help="policy yaml path (repeatable)")
    parser.add_argument("--workload", action="append", default=[], help="workload yaml path (repeatable)")
    parser.add_argument("--repeats", type=int, default=None, help="override repeat count")
    parser.add_argument("--seed-base", type=int, default=None, help="override base seed")
    parser.add_argument("--out-dir", default="", help="output directory override")
    parser.add_argument("--max-runs", type=int, default=0, help="optional hard cap for quick runs")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when any run fails")
    parser.add_argument("--compact", action="store_true", help="print compact json")
    parser.add_argument("--json", action="store_true", help="print session report as json")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    base_path = _resolve_path(args.base)
    if not base_path.exists():
        print(f"Error: base config not found: {base_path}", file=sys.stderr)
        return 2
    base_cfg = _load_yaml(base_path)

    policy_paths = [_resolve_path(x) for x in args.policy] if args.policy else _discover(DEFAULT_POLICY_GLOB)
    workload_paths = [_resolve_path(x) for x in args.workload] if args.workload else _discover(DEFAULT_WORKLOAD_GLOB)
    if not policy_paths:
        print("Error: no policy yaml files found", file=sys.stderr)
        return 2
    if not workload_paths:
        print("Error: no workload yaml files found", file=sys.stderr)
        return 2

    policies = [_load_yaml(p) for p in policy_paths]
    workloads = [_load_yaml(w) for w in workload_paths]

    for idx, p in enumerate(policies):
        _require_string(p.get("policy_id"), name=f"policy[{idx}].policy_id")
    for idx, w in enumerate(workloads):
        _require_string(w.get("workload_id"), name=f"workload[{idx}].workload_id")

    repeats = _as_int(args.repeats if args.repeats is not None else base_cfg.get("repeats", 1), default=1, minimum=1)
    seed_base = _as_int(
        args.seed_base if args.seed_base is not None else base_cfg.get("seed_base", 0),
        default=0,
    )
    out_dir = _resolve_path(args.out_dir) if str(args.out_dir).strip() else _resolve_path(
        str(base_cfg.get("output_dir", "outputs/experiments/backpressure_fairness"))
    )
    session_dir = out_dir / f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    session_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    failed = 0
    run_count = 0
    max_runs = _as_int(args.max_runs, default=0, minimum=0)
    for policy_idx, policy_cfg in enumerate(policies):
        policy_id = str(policy_cfg["policy_id"])
        for workload_idx, workload_cfg in enumerate(workloads):
            workload_id = str(workload_cfg["workload_id"])
            for repeat in range(repeats):
                run_count += 1
                if max_runs > 0 and run_count > max_runs:
                    break
                seed = int(seed_base + repeat * 1_000_000 + policy_idx * 10_000 + workload_idx)
                run_id = f"run_{policy_id}_{workload_id}_r{repeat:02d}_s{seed}"
                row = _run_once(
                    base_cfg=base_cfg,
                    policy_cfg=policy_cfg,
                    workload_cfg=workload_cfg,
                    repeat=repeat,
                    seed=seed,
                    session_dir=session_dir,
                    run_id=run_id,
                )
                rows.append(row)
                if row["status"] != "ok":
                    failed += 1
            if max_runs > 0 and run_count > max_runs:
                break
        if max_runs > 0 and run_count > max_runs:
            break

    payload = {
        "schema_version": SCHEMA_VERSION,
        "ts": _utc_now_iso(),
        "experiment_id": str(base_cfg.get("experiment_id", "backpressure_fairness")),
        "base_config": str(base_path),
        "policy_files": [str(p) for p in policy_paths],
        "workload_files": [str(w) for w in workload_paths],
        "repeats": int(repeats),
        "seed_base": int(seed_base),
        "total_runs": len(rows),
        "failed_runs": int(failed),
        "session_dir": str(session_dir),
        "runs": rows,
    }
    session_report = session_dir / "session_report.json"
    session_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if bool(args.json):
        if bool(args.compact):
            print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"session_dir={session_dir}")
        print(f"total_runs={payload['total_runs']} failed_runs={payload['failed_runs']}")
        print(f"session_report={session_report}")

    if bool(args.strict) and failed > 0:
        return 1
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
