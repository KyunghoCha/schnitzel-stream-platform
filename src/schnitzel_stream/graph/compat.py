from __future__ import annotations

"""
Static compatibility validation for node graphs (Phase 1 draft).

Intent:
- Separate topology validation (cycles/duplicates) from semantic compatibility checks.
- Keep the first iteration minimal and migration-friendly:
  - validate node kinds (source/node/sink) against edge directions
  - validate edge port labels (syntax only; existence/type is Phase 1.6+)
  - validate transport compatibility for the current runtime lane (default: in-proc)
  - validate packet kind compatibility using best-effort plugin-declared contracts
"""

from collections import defaultdict
import re
from typing import Any

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec
from schnitzel_stream.plugins.registry import PluginRegistry


class GraphCompatibilityError(ValueError):
    pass


_ALLOWED_NODE_KINDS = ("source", "node", "sink", "delay", "initial")
_PORT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NON_PORTABLE_KINDS = {"frame", "bytes"}  # best-effort v1: in-proc only until a blob/handle strategy exists


def _norm(raw: str) -> str:
    return str(raw or "").strip()


def _parse_kinds(raw: Any, *, attr: str, plugin: str) -> set[str] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        k = _norm(raw)
        return {k} if k else None
    if isinstance(raw, (list, tuple, set)):
        out: set[str] = set()
        for item in raw:
            if not isinstance(item, str):
                raise GraphCompatibilityError(f"{plugin} {attr} must contain strings only")
            k = _norm(item)
            if k:
                out.add(k)
        return out or None
    raise GraphCompatibilityError(f"{plugin} {attr} must be a string or list of strings")


def _is_wildcard(kinds: set[str] | None) -> bool:
    return kinds is None or "*" in kinds


def validate_ports(edges: list[EdgeSpec]) -> None:
    """Validate edge port labels (syntax only)."""

    for e in edges:
        for label, port in (("src_port", e.src_port), ("dst_port", e.dst_port)):
            if port is None:
                continue
            p = _norm(port)
            if not p:
                raise GraphCompatibilityError(f"edge {label} must not be empty")
            if not _PORT_RE.match(p):
                raise GraphCompatibilityError(f"edge {label} is not a valid identifier: {p}")


def validate_kind_direction(nodes: list[NodeSpec], edges: list[EdgeSpec]) -> None:
    """Validate node kind vs edge direction semantics."""

    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        incoming[e.dst].append(e.src)
        outgoing[e.src].append(e.dst)

    for n in nodes:
        kind = _norm(n.kind) or "node"
        if kind not in _ALLOWED_NODE_KINDS:
            raise GraphCompatibilityError(f"unsupported node kind: {n.kind} (supported: {_ALLOWED_NODE_KINDS})")
        if kind == "source" and incoming.get(n.node_id):
            raise GraphCompatibilityError(f"source node must not have incoming edges: {n.node_id}")
        if kind == "sink" and outgoing.get(n.node_id):
            raise GraphCompatibilityError(f"sink node must not have outgoing edges: {n.node_id}")


def validate_transport(nodes: list[NodeSpec], *, transport: str = "inproc") -> None:
    """Validate node transport lane compatibility (config-level)."""

    expected = _norm(transport) or "inproc"
    for n in nodes:
        raw = n.config.get("transport")
        if raw is None:
            continue
        t = _norm(raw)
        if not t:
            raise GraphCompatibilityError(f"node transport must not be empty: {n.node_id}")
        if t != expected:
            raise GraphCompatibilityError(f"node transport mismatch: node={n.node_id} transport={t} expected={expected}")


def validate_plugin_contracts(
    nodes: list[NodeSpec],
    edges: list[EdgeSpec],
    *,
    registry: PluginRegistry | None = None,
) -> None:
    """Validate best-effort plugin contracts (interface + packet kind compatibility)."""

    reg = registry or PluginRegistry()

    in_kinds: dict[str, set[str] | None] = {}
    out_kinds: dict[str, set[str] | None] = {}
    requires_portable_input: dict[str, bool] = {}

    for n in nodes:
        target = reg.resolve(n.plugin)
        if not isinstance(target, type):
            # Intent:
            # - Phase 1 runtime instantiates node plugins from classes.
            # - Factories can be reintroduced later once the validator/runtime contracts are stable.
            raise GraphCompatibilityError(f"node plugin must resolve to a class (Phase 1): {n.plugin}")

        if _norm(n.kind) == "source":
            if not callable(getattr(target, "run", None)):
                raise GraphCompatibilityError(f"source node plugin must implement run(): {n.plugin}")
        else:
            if not callable(getattr(target, "process", None)):
                raise GraphCompatibilityError(f"node plugin must implement process(): {n.plugin}")

        declared_in = _parse_kinds(getattr(target, "INPUT_KINDS", None), attr="INPUT_KINDS", plugin=n.plugin)
        declared_out = _parse_kinds(getattr(target, "OUTPUT_KINDS", None), attr="OUTPUT_KINDS", plugin=n.plugin)
        in_kinds[n.node_id] = declared_in
        out_kinds[n.node_id] = declared_out
        requires_portable_input[n.node_id] = bool(getattr(target, "REQUIRES_PORTABLE_PAYLOAD", False))

    for e in edges:
        src_out = out_kinds.get(e.src)
        dst_in = in_kinds.get(e.dst)

        if requires_portable_input.get(e.dst, False):
            # Best-effort v1 portability check:
            # - If a node declares it requires portable payloads, reject known non-portable kinds.
            # - Runtime still enforces JSON serialization for durable lanes.
            if not _is_wildcard(src_out):
                assert src_out is not None
                if not src_out.isdisjoint(_NON_PORTABLE_KINDS):
                    raise GraphCompatibilityError(
                        "non-portable payload kind routed into portable-only node: "
                        f"{e.src} -> {e.dst} ({sorted(src_out)} includes {sorted(_NON_PORTABLE_KINDS)})"
                    )

        if _is_wildcard(src_out) or _is_wildcard(dst_in):
            continue
        assert src_out is not None
        assert dst_in is not None
        if src_out.isdisjoint(dst_in):
            raise GraphCompatibilityError(
                "packet kind mismatch: "
                f"{e.src} -> {e.dst} ({sorted(src_out)} not compatible with {sorted(dst_in)})"
            )


def validate_graph_compat(
    nodes: list[NodeSpec],
    edges: list[EdgeSpec],
    *,
    transport: str = "inproc",
    registry: PluginRegistry | None = None,
) -> None:
    """Validate semantic compatibility for a node graph (Phase 1.6 draft)."""

    validate_ports(edges)
    validate_kind_direction(nodes, edges)
    validate_transport(nodes, transport=transport)
    validate_plugin_contracts(nodes, edges, registry=registry)
