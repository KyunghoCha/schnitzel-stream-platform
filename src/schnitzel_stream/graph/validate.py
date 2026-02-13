from __future__ import annotations

"""
Graph validation utilities (Phase 1 draft).

Intent:
- Provide deterministic, testable validation of topology before any execution.
- Phase 1 starts with a strict DAG rule (no cycles).
- Future phases may allow restricted cycles (e.g., only if a Delay/Window node is present).
"""

from collections import defaultdict

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec


class GraphValidationError(ValueError):
    pass


def _norm_id(raw: str) -> str:
    return str(raw or "").strip()


def _build_adj(node_ids: set[str], edges: list[EdgeSpec]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        src = _norm_id(e.src)
        dst = _norm_id(e.dst)
        if not src or not dst:
            raise GraphValidationError("edge endpoints must not be empty")
        if src not in node_ids:
            raise GraphValidationError(f"edge src node not found: {src}")
        if dst not in node_ids:
            raise GraphValidationError(f"edge dst node not found: {dst}")
        adj[src].append(dst)
    # Ensure all nodes exist as keys for predictable iteration.
    for nid in node_ids:
        adj.setdefault(nid, [])
    return dict(adj)


def find_cycle(nodes: list[NodeSpec], edges: list[EdgeSpec]) -> list[str] | None:
    """Return one cycle path (node ids) if present, else None."""

    node_ids: list[str] = []
    seen: set[str] = set()
    for n in nodes:
        nid = _norm_id(n.node_id)
        if not nid:
            raise GraphValidationError("node_id must not be empty")
        if nid in seen:
            raise GraphValidationError(f"duplicate node_id: {nid}")
        seen.add(nid)
        node_ids.append(nid)

    adj = _build_adj(set(node_ids), edges)

    # DFS cycle detection with parent tracking.
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {nid: WHITE for nid in node_ids}
    parent: dict[str, str | None] = {nid: None for nid in node_ids}

    def _reconstruct_cycle(start: str, end: str) -> list[str]:
        # Reconstruct path end -> ... -> start -> end
        path = [end]
        cur = start
        while cur is not None and cur != end:
            path.append(cur)
            cur = parent.get(cur)
        path.append(end)
        path.reverse()
        return path

    def _dfs(u: str) -> list[str] | None:
        color[u] = GRAY
        for v in adj.get(u, []):
            if color[v] == WHITE:
                parent[v] = u
                cyc = _dfs(v)
                if cyc is not None:
                    return cyc
            elif color[v] == GRAY:
                # Back-edge detected: u -> v closes a cycle.
                parent[v] = u
                return _reconstruct_cycle(start=u, end=v)
        color[u] = BLACK
        return None

    for nid in node_ids:
        if color[nid] == WHITE:
            cyc = _dfs(nid)
            if cyc is not None:
                return cyc
    return None


def validate_graph(
    nodes: list[NodeSpec],
    edges: list[EdgeSpec],
    *,
    allow_cycles: bool = False,
) -> None:
    """Validate a node/edge graph for execution."""

    # Phase 1 default: strict DAG validation.
    cyc = find_cycle(nodes, edges)
    if cyc and not allow_cycles:
        raise GraphValidationError(f"graph contains a cycle (strict DAG mode): {' -> '.join(cyc)}")

