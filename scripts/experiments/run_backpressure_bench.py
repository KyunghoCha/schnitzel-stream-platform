#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any

from omegaconf import OmegaConf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.runtime.inproc import InProcGraphRunner
from _backpressure_common import (
    as_dict,
    as_float,
    as_int,
    as_list,
    deep_merge,
    discover,
    expected_counts,
    metrics_from_run,
    node_config,
    patch_node_config,
    read_jsonl,
    require_string,
    resolve_path,
    utc_now_iso,
)


SCHEMA_VERSION = 1
DEFAULT_BASE = "configs/experiments/backpressure_fairness/bench_base.yaml"
DEFAULT_POLICY_GLOB = "configs/experiments/backpressure_fairness/policy_*.yaml"
DEFAULT_WORKLOAD_GLOB = "configs/experiments/backpressure_fairness/workloads_*.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = OmegaConf.load(path)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"yaml must be a mapping: {path}")
    return dict(cont)


def _build_specs(graph: dict[str, Any]) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    nodes: list[NodeSpec] = []
    edges: list[EdgeSpec] = []

    for idx, item in enumerate(as_list(graph.get("nodes"))):
        row = as_dict(item)
        node_id = require_string(row.get("id", row.get("node_id")), name=f"graph.nodes[{idx}].id")
        plugin = require_string(row.get("plugin"), name=f"graph.nodes[{idx}].plugin")
        kind = require_string(row.get("kind", "node"), name=f"graph.nodes[{idx}].kind")
        config = as_dict(row.get("config"))
        nodes.append(NodeSpec(node_id=node_id, plugin=plugin, kind=kind, config=config))

    for idx, item in enumerate(as_list(graph.get("edges"))):
        row = as_dict(item)
        src = require_string(row.get("from", row.get("src")), name=f"graph.edges[{idx}].from")
        dst = require_string(row.get("to", row.get("dst")), name=f"graph.edges[{idx}].to")
        src_port = row.get("from_port", row.get("src_port"))
        dst_port = row.get("to_port", row.get("dst_port"))
        src_port_val = str(src_port).strip() if isinstance(src_port, str) and src_port.strip() else None
        dst_port_val = str(dst_port).strip() if isinstance(dst_port, str) and dst_port.strip() else None
        edges.append(EdgeSpec(src=src, dst=dst, src_port=src_port_val, dst_port=dst_port_val))
    return nodes, edges


def _run_once(
    *,
    base_cfg: dict[str, Any],
    policy_cfg: dict[str, Any],
    workload_cfg: dict[str, Any],
    repeat: int,
    seed: int,
    session_dir: Path,
) -> dict[str, Any]:
    graph = copy.deepcopy(as_dict(base_cfg.get("graph")))
    node_ids = deep_merge(
        {
            "source": "src",
            "burst": "burst",
            "processor": "processor",
            "sink": "sink",
        },
        as_dict(base_cfg.get("node_ids")),
    )
    source_node_id = str(node_ids["source"])
    burst_node_id = str(node_ids["burst"])
    processor_node_id = str(node_ids["processor"])
    sink_node_id = str(node_ids["sink"])

    for node_id, patch in as_dict(workload_cfg.get("node_overrides")).items():
        patch_node_config(graph, node_id=str(node_id), patch=as_dict(patch))
    for node_id, patch in as_dict(policy_cfg.get("node_overrides")).items():
        patch_node_config(graph, node_id=str(node_id), patch=as_dict(patch))

    source_patch = as_dict(workload_cfg.get("source_config"))
    burst_patch = as_dict(workload_cfg.get("burst_config"))
    processor_patch = as_dict(workload_cfg.get("processor_config"))
    sink_patch = as_dict(workload_cfg.get("sink_config"))
    if source_patch:
        patch_node_config(graph, node_id=source_node_id, patch=source_patch)
    if burst_patch:
        patch_node_config(graph, node_id=burst_node_id, patch=burst_patch)
    if processor_patch:
        patch_node_config(graph, node_id=processor_node_id, patch=processor_patch)
    if sink_patch:
        patch_node_config(graph, node_id=sink_node_id, patch=sink_patch)

    patch_node_config(graph, node_id=source_node_id, patch={"seed": int(seed)})
    patch_node_config(graph, node_id=processor_node_id, patch={"seed": int(seed + 977)})

    policy_id = str(policy_cfg.get("policy_id", "unknown"))
    workload_id = str(workload_cfg.get("workload_id", "unknown"))
    run_id = f"run_{policy_id}_{workload_id}_r{repeat:02d}_s{seed}"

    events_dir = session_dir / "events"
    runs_dir = session_dir / "runs"
    events_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    events_path = events_dir / f"{run_id}.jsonl"
    patch_node_config(graph, node_id=sink_node_id, patch={"output_path": str(events_path)})

    nodes, edges = _build_specs(graph)

    latency_budget_ms = as_float(
        workload_cfg.get("latency_budget_ms", base_cfg.get("latency_budget_ms", 100.0)),
        default=100.0,
        minimum=1.0,
    )

    source_cfg = node_config(graph, node_id=source_node_id)
    burst_cfg = node_config(graph, node_id=burst_node_id)
    sink_cfg = node_config(graph, node_id=sink_node_id)
    expected_total, expected_by_group = expected_counts(source_cfg=source_cfg, burst_cfg=burst_cfg, seed=int(seed))
    group_weights = {
        str(k): float(v)
        for k, v in as_dict(sink_cfg.get("group_weights")).items()
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

    records = read_jsonl(events_path)
    metrics, breakdown = metrics_from_run(
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
        "ts": utc_now_iso(),
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

    base_path = resolve_path(project_root=PROJECT_ROOT, raw=args.base)
    if not base_path.exists():
        print(f"Error: base config not found: {base_path}", file=sys.stderr)
        return 2
    base_cfg = _load_yaml(base_path)

    policy_paths = [resolve_path(project_root=PROJECT_ROOT, raw=x) for x in args.policy] if args.policy else discover(project_root=PROJECT_ROOT, pattern=DEFAULT_POLICY_GLOB)
    workload_paths = [resolve_path(project_root=PROJECT_ROOT, raw=x) for x in args.workload] if args.workload else discover(project_root=PROJECT_ROOT, pattern=DEFAULT_WORKLOAD_GLOB)
    if not policy_paths:
        print("Error: no policy yaml files found", file=sys.stderr)
        return 2
    if not workload_paths:
        print("Error: no workload yaml files found", file=sys.stderr)
        return 2

    policies = [_load_yaml(p) for p in policy_paths]
    workloads = [_load_yaml(w) for w in workload_paths]

    for idx, p in enumerate(policies):
        require_string(p.get("policy_id"), name=f"policy[{idx}].policy_id")
    for idx, w in enumerate(workloads):
        require_string(w.get("workload_id"), name=f"workload[{idx}].workload_id")

    repeats = as_int(args.repeats if args.repeats is not None else base_cfg.get("repeats", 1), default=1, minimum=1)
    seed_base = as_int(
        args.seed_base if args.seed_base is not None else base_cfg.get("seed_base", 0),
        default=0,
    )
    out_dir = resolve_path(project_root=PROJECT_ROOT, raw=args.out_dir) if str(args.out_dir).strip() else resolve_path(
        project_root=PROJECT_ROOT,
        raw=str(base_cfg.get("output_dir", "outputs/experiments/backpressure_fairness")),
    )
    session_dir = out_dir / f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    session_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    failed = 0
    run_count = 0
    max_runs = as_int(args.max_runs, default=0, minimum=0)
    for policy_idx, policy_cfg in enumerate(policies):
        policy_id = str(policy_cfg["policy_id"])
        for workload_idx, workload_cfg in enumerate(workloads):
            workload_id = str(workload_cfg["workload_id"])
            for repeat in range(repeats):
                run_count += 1
                if max_runs > 0 and run_count > max_runs:
                    break
                seed = int(seed_base + repeat * 1_000_000 + policy_idx * 10_000 + workload_idx)
                row = _run_once(
                    base_cfg=base_cfg,
                    policy_cfg=policy_cfg,
                    workload_cfg=workload_cfg,
                    repeat=repeat,
                    seed=seed,
                    session_dir=session_dir,
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
        "ts": utc_now_iso(),
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
