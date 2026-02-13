from __future__ import annotations

"""
In-process graph execution (Phase 1 MVP).

Intent:
- Execute a v2 node/edge graph in a single process for rapid iteration on edge devices.
- Strict DAG only (no cycles) in Phase 1; restricted cycles are planned in `P1.7`.
- No transport layer yet; nodes exchange StreamPackets in-memory (side-effects are implemented by node plugins).
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
import inspect
from typing import Any, Iterable

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.graph.validate import GraphValidationError, validate_graph
from schnitzel_stream.packet import StreamPacket
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.control.throttle import NoopThrottle, ThrottlePolicy


class GraphExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionResult:
    outputs_by_node: dict[str, list[StreamPacket]]
    metrics: dict[str, int] = field(default_factory=dict)


def _topological_order(nodes: list[NodeSpec], edges: list[EdgeSpec]) -> list[str]:
    node_ids = [n.node_id for n in nodes]
    indeg: dict[str, int] = {nid: 0 for nid in node_ids}
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for e in edges:
        adj[e.src].append(e.dst)
        indeg[e.dst] += 1

    # Deterministic order:
    # - seed queue using the node declaration order
    # - process adjacency in edge declaration order
    q: deque[str] = deque([nid for nid in node_ids if indeg[nid] == 0])
    out: list[str] = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in adj.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    if len(out) != len(node_ids):
        raise GraphValidationError("graph is not a DAG (topological sort failed)")
    return out


def _build_factory_kwargs(factory: Any, spec: NodeSpec) -> dict[str, Any]:
    try:
        sig = inspect.signature(factory)
    except (TypeError, ValueError):
        return {}

    params = sig.parameters
    accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())

    kwargs: dict[str, Any] = {}
    if accepts_kwargs or "node_id" in params:
        kwargs["node_id"] = spec.node_id
    if accepts_kwargs or "config" in params:
        kwargs["config"] = dict(spec.config)
    return kwargs


def _instantiate_node(registry: PluginRegistry, spec: NodeSpec) -> Any:
    target = registry.resolve(spec.plugin)
    if not callable(target):
        return target

    kwargs = _build_factory_kwargs(target, spec)

    # Intent:
    # - Prefer passing `node_id`/`config` when the factory accepts it.
    # - Fall back to no-arg construction for backwards-compatibility with older plugins.
    try:
        return target(**kwargs)  # type: ignore[misc]
    except TypeError:
        return target()  # type: ignore[misc]


class InProcGraphRunner:
    def __init__(self, *, registry: PluginRegistry | None = None) -> None:
        self._registry = registry or PluginRegistry()

    def run(
        self,
        *,
        nodes: list[NodeSpec],
        edges: list[EdgeSpec],
        throttle: ThrottlePolicy | None = None,
    ) -> ExecutionResult:
        validate_graph(nodes, edges, allow_cycles=False)
        validate_graph_compat(nodes, edges, transport="inproc", registry=self._registry)

        th = throttle or NoopThrottle()

        nodes_by_id: dict[str, NodeSpec] = {n.node_id: n for n in nodes}
        outputs_by_node: dict[str, list[StreamPacket]] = {nid: [] for nid in nodes_by_id}
        consumed_by_node: dict[str, int] = {nid: 0 for nid in nodes_by_id}
        produced_by_node: dict[str, int] = {nid: 0 for nid in nodes_by_id}
        source_emitted_total = 0

        outgoing: dict[str, list[str]] = defaultdict(list)
        for e in edges:
            outgoing[e.src].append(e.dst)

        order = _topological_order(nodes, edges)

        inbox: dict[str, deque[StreamPacket]] = {nid: deque() for nid in nodes_by_id}
        instances: dict[str, Any] = {}
        for n in nodes:
            instances[n.node_id] = _instantiate_node(self._registry, n)

        def _emit(src_id: str, pkt: StreamPacket) -> None:
            for dst_id in outgoing.get(src_id, []):
                inbox[dst_id].append(pkt)

        try:
            for nid in order:
                node_spec = nodes_by_id[nid]
                inst = instances[nid]

                if node_spec.kind == "source":
                    run_fn = getattr(inst, "run", None)
                    if not callable(run_fn):
                        raise TypeError(f"source node does not implement run(): {node_spec.plugin}")
                    produced = run_fn()
                    if produced is None:
                        raise TypeError(f"source node run() must return Iterable[StreamPacket]: {node_spec.plugin}")
                    if not th.allow_source_emit(node_id=nid, emitted_total=source_emitted_total):
                        continue
                    for pkt in produced:
                        if not th.allow_source_emit(node_id=nid, emitted_total=source_emitted_total):
                            break
                        if not isinstance(pkt, StreamPacket):
                            raise TypeError(f"node output must be StreamPacket: {node_spec.plugin}")
                        outputs_by_node[nid].append(pkt)
                        produced_by_node[nid] += 1
                        source_emitted_total += 1
                        _emit(nid, pkt)
                    continue

                process_fn = getattr(inst, "process", None)
                if not callable(process_fn):
                    raise TypeError(f"node does not implement process(): {node_spec.plugin}")

                while inbox[nid]:
                    inp = inbox[nid].popleft()
                    consumed_by_node[nid] += 1
                    produced = process_fn(inp)
                    if produced is None:
                        raise TypeError(f"node process() must return Iterable[StreamPacket]: {node_spec.plugin}")
                    for pkt in produced:
                        if not isinstance(pkt, StreamPacket):
                            raise TypeError(f"node output must be StreamPacket: {node_spec.plugin}")
                        outputs_by_node[nid].append(pkt)
                        produced_by_node[nid] += 1
                        _emit(nid, pkt)

            metrics: dict[str, int] = {
                "packets.consumed_total": sum(consumed_by_node.values()),
                "packets.produced_total": sum(produced_by_node.values()),
                "packets.source_emitted_total": int(source_emitted_total),
            }
            for node_id, n in nodes_by_id.items():
                metrics[f"node.{node_id}.consumed"] = int(consumed_by_node[node_id])
                metrics[f"node.{node_id}.produced"] = int(produced_by_node[node_id])
                # Keep kind as a numeric tag until a richer report contract lands.
                metrics[f"node.{node_id}.is_source"] = 1 if n.kind == "source" else 0
                metrics[f"node.{node_id}.is_sink"] = 1 if n.kind == "sink" else 0

            for node_id, inst in instances.items():
                extra_fn = getattr(inst, "metrics", None)
                if not callable(extra_fn):
                    continue
                extra = extra_fn()
                if not isinstance(extra, dict):
                    continue
                for k, v in extra.items():
                    if not isinstance(k, str) or not k.strip():
                        continue
                    if not isinstance(v, int) or isinstance(v, bool):
                        continue
                    metrics[f"node.{node_id}.{k.strip()}"] = int(v)

            return ExecutionResult(outputs_by_node=outputs_by_node, metrics=metrics)
        finally:
            # Best-effort cleanup, regardless of partial execution failures.
            for inst in instances.values():
                close_fn = getattr(inst, "close", None)
                if callable(close_fn):
                    close_fn()
