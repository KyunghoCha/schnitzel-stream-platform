#!/usr/bin/env python3
# Docs: docs/ops/command_reference.md
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys
import threading
import time
from typing import Any

from omegaconf import OmegaConf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from schnitzel_stream.packs.experiments.nodes.backpressure import generate_event_plan
from _backpressure_common import (
    as_dict,
    as_float,
    as_int,
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
DEFAULT_OUT_DIR = "outputs/experiments/backpressure_fairness/ros2_baseline"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = OmegaConf.load(path)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"yaml must be a mapping: {path}")
    return dict(cont)


def _import_ros2_modules() -> tuple[Any, Any, Any]:
    import importlib

    rclpy = importlib.import_module("rclpy")
    exec_mod = importlib.import_module("rclpy.executors")
    std_msgs = importlib.import_module("std_msgs.msg")
    return rclpy, exec_mod.MultiThreadedExecutor, std_msgs.String


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _json_loads(raw: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(str(raw))
    except json.JSONDecodeError:
        return None
    return dict(obj) if isinstance(obj, dict) else None


def _weight_for_packet(
    *,
    packet: dict[str, Any],
    weight_key: str,
    default_weight: float,
    value_weights: dict[str, float],
) -> float:
    payload = as_dict(packet.get("payload"))
    meta = as_dict(packet.get("meta"))
    raw = meta.get(weight_key)
    if raw is None:
        raw = payload.get(weight_key)
    return float(value_weights.get(str(raw), default_weight))


def _select_weighted_drop_index(
    *,
    queue: list[dict[str, Any]],
    weight_key: str,
    default_weight: float,
    value_weights: dict[str, float],
) -> int:
    best_idx = 0
    best_weight = float("inf")
    for idx, packet in enumerate(queue):
        weight = _weight_for_packet(
            packet=packet,
            weight_key=weight_key,
            default_weight=default_weight,
            value_weights=value_weights,
        )
        if weight < best_weight:
            best_idx = idx
            best_weight = weight
    return int(best_idx)


def _apply_overflow_policy(
    *,
    queue: list[dict[str, Any]],
    incoming: dict[str, Any],
    inbox_max: int,
    overflow_policy: str,
    weight_key: str,
    default_weight: float,
    value_weights: dict[str, float],
) -> tuple[bool, int, str]:
    if int(inbox_max) <= 0 or len(queue) < int(inbox_max):
        queue.append(incoming)
        return True, 0, ""

    policy = str(overflow_policy or "drop_new").strip().lower()
    if policy == "error":
        return False, 0, f"inbox overflow: node=processor max={int(inbox_max)} policy=error (src=source)"
    if policy == "drop_oldest":
        queue.pop(0)
        queue.append(incoming)
        return True, 1, ""
    if policy == "weighted_drop":
        idx = _select_weighted_drop_index(
            queue=queue,
            weight_key=weight_key,
            default_weight=default_weight,
            value_weights=value_weights,
        )
        queue.pop(int(idx))
        queue.append(incoming)
        return True, 1, ""

    return False, 1, ""


class _SourcePublisherNode:
    def __init__(self, *, rclpy: Any, string_cls: Any, topic: str, qos_depth: int) -> None:
        self._rclpy = rclpy
        self._node = rclpy.create_node("ss_bench_source")
        self._pub = self._node.create_publisher(string_cls, topic, int(max(1, qos_depth)))
        self._string_cls = string_cls
        self.published_total = 0

    @property
    def node(self) -> Any:
        return self._node

    def publish_events(
        self,
        *,
        source_cfg: dict[str, Any],
        seed: int,
        burst_count: int,
        expected_total: int,
        stop_event: threading.Event,
        has_error: callable,
    ) -> None:
        plan = generate_event_plan(source_cfg, seed=int(seed))
        source_id = str(source_cfg.get("source_id", "fairness_lab"))
        emit_sleep_ms = as_float(source_cfg.get("emit_sleep_ms", 0.0), default=0.0, minimum=0.0)
        outage_sleep_ms = as_float(source_cfg.get("outage_sleep_ms", 0.0), default=0.0, minimum=0.0)
        signal_scale = as_float(source_cfg.get("signal_scale", 1.0), default=1.0, minimum=0.0)

        for item in plan:
            if stop_event.is_set() or bool(has_error()):
                return
            if bool(getattr(item, "recovery_marker", False)) and outage_sleep_ms > 0.0:
                time.sleep(outage_sleep_ms / 1000.0)
            for burst_seq in range(max(1, int(burst_count))):
                if stop_event.is_set() or bool(has_error()):
                    return
                emitted_ns = int(time.monotonic_ns())
                payload = {
                    "event_id": f"{source_id}:{int(item.seq):08d}",
                    "seq": int(item.seq),
                    "group_id": str(item.group_id),
                    "logical_ts_ms": float(item.logical_ts_ms),
                    "signal": float((int(item.seq) % 10) / 10.0) * float(signal_scale),
                    "source_id": source_id,
                }
                meta = {
                    "seq": int(item.seq),
                    "group_id": str(item.group_id),
                    "recovery_marker": bool(item.recovery_marker),
                    "emitted_mono_ns": emitted_ns,
                    "expected_total": int(expected_total),
                    "burst_seq": int(burst_seq),
                }
                msg = self._string_cls()
                msg.data = _json_dumps({"payload": payload, "meta": meta})
                self._pub.publish(msg)
                self.published_total += 1
            if emit_sleep_ms > 0.0:
                time.sleep(emit_sleep_ms / 1000.0)

    def close(self) -> None:
        destroy_fn = getattr(self._node, "destroy_node", None)
        if callable(destroy_fn):
            destroy_fn()


class _ProcessorNode:
    def __init__(
        self,
        *,
        rclpy: Any,
        string_cls: Any,
        in_topic: str,
        out_topic: str,
        qos_depth: int,
        processor_cfg: dict[str, Any],
    ) -> None:
        self._rclpy = rclpy
        self._string_cls = string_cls
        self._node = rclpy.create_node("ss_bench_processor")
        self._pub = self._node.create_publisher(string_cls, out_topic, int(max(1, qos_depth)))
        self._sub = self._node.create_subscription(string_cls, in_topic, self._on_msg, int(max(1, qos_depth)))

        runtime_cfg = as_dict(processor_cfg.get("__runtime__"))
        self._inbox_max = as_int(runtime_cfg.get("inbox_max", 0), default=0, minimum=0)
        overflow = str(runtime_cfg.get("inbox_overflow", "drop_new")).strip().lower()
        self._overflow_policy = overflow if overflow else "drop_new"
        self._overflow_weight_key = str(runtime_cfg.get("overflow_weight_key", "group_id")).strip() or "group_id"
        self._overflow_default_weight = as_float(runtime_cfg.get("overflow_default_weight", 1.0), default=1.0)
        self._overflow_weights = {
            str(k): as_float(v, default=1.0)
            for k, v in as_dict(runtime_cfg.get("overflow_weights")).items()
            if str(k).strip()
        }

        self._delay_ms = as_float(processor_cfg.get("delay_ms", 1.5), default=1.5, minimum=0.0)
        self._jitter_ms = as_float(processor_cfg.get("jitter_ms", 0.0), default=0.0, minimum=0.0)
        self._group_delay_ms = {
            str(k): as_float(v, default=0.0, minimum=0.0)
            for k, v in as_dict(processor_cfg.get("group_delay_ms")).items()
        }
        seed = as_int(processor_cfg.get("seed", 0), default=0)
        self._rng = random.Random(int(seed))

        self._queue: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        self._active_worker = 0
        self.received_total = 0
        self.forwarded_total = 0
        self.dropped_total = 0
        self.overflow_error_total = 0
        self.error_message = ""

    @property
    def node(self) -> Any:
        return self._node

    def _on_msg(self, msg: Any) -> None:
        payload = _json_loads(getattr(msg, "data", ""))
        if payload is None:
            return

        packet = {
            "payload": as_dict(payload.get("payload")),
            "meta": as_dict(payload.get("meta")),
        }

        with self._lock:
            self.received_total += 1
            accepted, dropped, err = _apply_overflow_policy(
                queue=self._queue,
                incoming=packet,
                inbox_max=self._inbox_max,
                overflow_policy=self._overflow_policy,
                weight_key=self._overflow_weight_key,
                default_weight=self._overflow_default_weight,
                value_weights=self._overflow_weights,
            )
            self.dropped_total += int(max(0, dropped))
            if err:
                self.overflow_error_total += 1
                self.error_message = str(err)
                self._stop.set()
                return
            if not accepted:
                return

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            packet: dict[str, Any] | None = None
            with self._lock:
                if self._queue:
                    packet = self._queue.pop(0)
                    self._active_worker = 1
                else:
                    self._active_worker = 0

            if packet is None:
                time.sleep(0.001)
                continue

            payload = dict(as_dict(packet.get("payload")))
            meta = dict(as_dict(packet.get("meta")))
            group_id = str(payload.get("group_id", meta.get("group_id", "group_a")))

            delay_ms = self._delay_ms + float(self._group_delay_ms.get(group_id, 0.0))
            if self._jitter_ms > 0.0:
                delay_ms += self._rng.uniform(-self._jitter_ms, self._jitter_ms)
            if delay_ms > 0.0:
                time.sleep(delay_ms / 1000.0)

            signal = as_float(payload.get("signal"), default=0.0)
            seq = as_int(payload.get("seq"), default=0)
            payload["risk_score"] = round(float(signal) * 0.75 + (int(seq) % 5) * 0.05, 6)
            payload["policy_group"] = group_id
            meta["processed_mono_ns"] = int(time.monotonic_ns())

            out_msg = self._string_cls()
            out_msg.data = _json_dumps({"payload": payload, "meta": meta})
            self._pub.publish(out_msg)
            self.forwarded_total += 1

        with self._lock:
            self._active_worker = 0

    def has_error(self) -> bool:
        return bool(self.error_message)

    def queue_size(self) -> int:
        with self._lock:
            return int(len(self._queue))

    def is_idle(self) -> bool:
        with self._lock:
            return len(self._queue) == 0 and int(self._active_worker) == 0

    def close(self) -> None:
        self._stop.set()
        self._worker.join(timeout=2.0)
        destroy_fn = getattr(self._node, "destroy_node", None)
        if callable(destroy_fn):
            destroy_fn()


class _SinkNode:
    def __init__(self, *, rclpy: Any, string_cls: Any, in_topic: str, qos_depth: int, events_path: Path) -> None:
        self._node = rclpy.create_node("ss_bench_sink")
        self._sub = self._node.create_subscription(string_cls, in_topic, self._on_msg, int(max(1, qos_depth)))
        self._events_path = events_path
        self._events_path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._events_path.open("w", encoding="utf-8")
        self.received_total = 0

    @property
    def node(self) -> Any:
        return self._node

    def _on_msg(self, msg: Any) -> None:
        obj = _json_loads(getattr(msg, "data", ""))
        if obj is None:
            return
        payload = as_dict(obj.get("payload"))
        meta = as_dict(obj.get("meta"))
        now_ns = int(time.monotonic_ns())

        seq = as_int(payload.get("seq", meta.get("seq", -1)), default=-1)
        group_id = str(payload.get("group_id", meta.get("group_id", "unknown")))
        emitted_ns = as_int(meta.get("emitted_mono_ns"), default=0, minimum=0)
        latency_ms = ((now_ns - emitted_ns) / 1_000_000.0) if emitted_ns > 0 else None
        marker = bool(meta.get("recovery_marker", False))

        rec = {
            "node_id": "metrics_sink_ros2",
            "packet_id": str(meta.get("packet_id", f"ros2:{seq}:{self.received_total}")),
            "seq": int(seq),
            "group_id": group_id,
            "source_id": str(payload.get("source_id", "fairness_lab")),
            "kind": "event",
            "logical_ts_ms": as_float(payload.get("logical_ts_ms"), default=0.0, minimum=0.0),
            "latency_ms": None if latency_ms is None else float(latency_ms),
            "observed_mono_ns": int(now_ns),
            "emitted_mono_ns": int(emitted_ns),
            "recovery_marker": marker,
        }
        self._fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._fh.flush()
        self.received_total += 1

    def close(self) -> None:
        fh = getattr(self, "_fh", None)
        if fh is not None:
            fh.close()
        destroy_fn = getattr(self._node, "destroy_node", None)
        if callable(destroy_fn):
            destroy_fn()


def _run_ros2_once(
    *,
    graph: dict[str, Any],
    base_cfg: dict[str, Any],
    policy_cfg: dict[str, Any],
    workload_cfg: dict[str, Any],
    repeat: int,
    seed: int,
    session_dir: Path,
    timeout_sec: float,
) -> dict[str, Any]:
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

    policy_id = str(policy_cfg.get("policy_id", "unknown"))
    workload_id = str(workload_cfg.get("workload_id", "unknown"))
    run_id = f"run_{policy_id}_{workload_id}_r{repeat:02d}_s{seed}"

    patch_node_config(graph, node_id=source_node_id, patch={"seed": int(seed)})
    patch_node_config(graph, node_id=processor_node_id, patch={"seed": int(seed + 977)})

    events_dir = session_dir / "events"
    runs_dir = session_dir / "runs"
    events_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    events_path = events_dir / f"{run_id}.jsonl"
    patch_node_config(graph, node_id=sink_node_id, patch={"output_path": str(events_path)})

    source_cfg = node_config(graph, node_id=source_node_id)
    burst_cfg = node_config(graph, node_id=burst_node_id)
    processor_cfg = node_config(graph, node_id=processor_node_id)
    sink_cfg = node_config(graph, node_id=sink_node_id)

    expected_total, expected_by_group = expected_counts(source_cfg=source_cfg, burst_cfg=burst_cfg, seed=int(seed))
    burst_count = as_int(burst_cfg.get("count", 1), default=1, minimum=1)
    group_weights = {
        str(k): float(v)
        for k, v in as_dict(sink_cfg.get("group_weights")).items()
        if isinstance(v, (int, float))
    }
    latency_budget_ms = as_float(
        workload_cfg.get("latency_budget_ms", base_cfg.get("latency_budget_ms", 100.0)),
        default=100.0,
        minimum=1.0,
    )

    status = "ok"
    err = ""
    runtime_metrics: dict[str, int] = {}

    rclpy = None
    executor = None
    spin_thread = None
    source_node = None
    processor_node = None
    sink_node = None

    started_ns = time.monotonic_ns()
    try:
        rclpy, executor_cls, string_cls = _import_ros2_modules()

        rclpy.init(args=None)
        executor = executor_cls(num_threads=4)

        topic_prefix = f"/ss_bench/{run_id}"
        source_topic = f"{topic_prefix}/source"
        processed_topic = f"{topic_prefix}/processed"
        qos_depth = 64

        source_node = _SourcePublisherNode(rclpy=rclpy, string_cls=string_cls, topic=source_topic, qos_depth=qos_depth)
        processor_node = _ProcessorNode(
            rclpy=rclpy,
            string_cls=string_cls,
            in_topic=source_topic,
            out_topic=processed_topic,
            qos_depth=qos_depth,
            processor_cfg=processor_cfg,
        )
        sink_node = _SinkNode(rclpy=rclpy, string_cls=string_cls, in_topic=processed_topic, qos_depth=qos_depth, events_path=events_path)

        executor.add_node(source_node.node)
        executor.add_node(processor_node.node)
        executor.add_node(sink_node.node)

        spin_thread = threading.Thread(target=executor.spin, daemon=True)
        spin_thread.start()

        stop_evt = threading.Event()
        source_node.publish_events(
            source_cfg=source_cfg,
            seed=int(seed),
            burst_count=burst_count,
            expected_total=expected_total,
            stop_event=stop_evt,
            has_error=processor_node.has_error,
        )

        wait_started = time.monotonic()
        stable_count = 0
        while True:
            if processor_node.has_error():
                status = "error"
                err = processor_node.error_message
                break
            now = time.monotonic()
            if now - wait_started > float(timeout_sec):
                status = "error"
                err = f"TimeoutError: run exceeded timeout_sec={float(timeout_sec):.3f}"
                break
            if processor_node.is_idle() and int(processor_node.forwarded_total) <= int(sink_node.received_total):
                stable_count += 1
            else:
                stable_count = 0
            if stable_count >= 20:
                break
            time.sleep(0.01)

    except Exception as exc:
        status = "error"
        err = f"{type(exc).__name__}: {exc}"
    finally:
        duration_sec = float((time.monotonic_ns() - started_ns) / 1_000_000_000.0)

        if processor_node is not None:
            runtime_metrics = {
                "packets.received_total": int(processor_node.received_total),
                "packets.forwarded_total": int(processor_node.forwarded_total),
                "packets.dropped_total": int(processor_node.dropped_total),
                "packets.overflow_error_total": int(processor_node.overflow_error_total),
            }
        if source_node is not None:
            runtime_metrics["source.published_total"] = int(source_node.published_total)
        if sink_node is not None:
            runtime_metrics["sink.received_total"] = int(sink_node.received_total)

        if executor is not None:
            shutdown_fn = getattr(executor, "shutdown", None)
            if callable(shutdown_fn):
                try:
                    shutdown_fn()
                except Exception:
                    pass
        if spin_thread is not None:
            spin_thread.join(timeout=2.0)
        if sink_node is not None:
            sink_node.close()
        if processor_node is not None:
            processor_node.close()
        if source_node is not None:
            source_node.close()
        if rclpy is not None:
            try:
                rclpy.shutdown()
            except Exception:
                pass

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
        "baseline_system": "ros2_transport",
        "paths": {
            "events_path": str(events_path),
        },
    }

    out_path = runs_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["paths"]["run_path"] = str(out_path)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ROS2 transport baseline benchmark workloads")
    parser.add_argument("--base", default=DEFAULT_BASE, help="base benchmark yaml")
    parser.add_argument("--policy", action="append", default=[], help="policy yaml path (repeatable)")
    parser.add_argument("--workload", action="append", default=[], help="workload yaml path (repeatable)")
    parser.add_argument("--repeats", type=int, default=None, help="override repeat count")
    parser.add_argument("--seed-base", type=int, default=None, help="override base seed")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="output directory override")
    parser.add_argument("--max-runs", type=int, default=0, help="optional hard cap for quick runs")
    parser.add_argument("--timeout-sec", type=float, default=180.0, help="single-run timeout seconds")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when any run fails")
    parser.add_argument("--compact", action="store_true", help="print compact json")
    parser.add_argument("--json", action="store_true", help="print session report as json")
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Preflight import check: this script must run on a ROS2-compatible python (typically /usr/bin/python3 for humble).
    try:
        _import_ros2_modules()
    except Exception as exc:
        print(f"Error: ROS2 python dependencies unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

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
    seed_base = as_int(args.seed_base if args.seed_base is not None else base_cfg.get("seed_base", 0), default=0)
    out_dir = resolve_path(project_root=PROJECT_ROOT, raw=args.out_dir) if str(args.out_dir).strip() else resolve_path(
        project_root=PROJECT_ROOT,
        raw=str(base_cfg.get("output_dir", DEFAULT_OUT_DIR)),
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
                graph = copy.deepcopy(as_dict(base_cfg.get("graph")))

                for node_id, patch in as_dict(workload_cfg.get("node_overrides")).items():
                    patch_node_config(graph, node_id=str(node_id), patch=as_dict(patch))
                for node_id, patch in as_dict(policy_cfg.get("node_overrides")).items():
                    patch_node_config(graph, node_id=str(node_id), patch=as_dict(patch))

                source_node_id = str(as_dict(base_cfg.get("node_ids")).get("source", "src"))
                burst_node_id = str(as_dict(base_cfg.get("node_ids")).get("burst", "burst"))
                processor_node_id = str(as_dict(base_cfg.get("node_ids")).get("processor", "processor"))
                sink_node_id = str(as_dict(base_cfg.get("node_ids")).get("sink", "sink"))

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

                row = _run_ros2_once(
                    graph=graph,
                    base_cfg=base_cfg,
                    policy_cfg=policy_cfg,
                    workload_cfg=workload_cfg,
                    repeat=repeat,
                    seed=seed,
                    session_dir=session_dir,
                    timeout_sec=float(max(1.0, float(args.timeout_sec))),
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
        "baseline_system": "ros2_transport",
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
