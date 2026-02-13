from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec


@dataclass(frozen=True)
class GraphSpec:
    """Graph specification (Phase 0 minimal).

    Intent:
    - Phase 0 uses a "job" indirection instead of a full DAG runtime.
    - This keeps the migration reversible while SSOT is still evolving.
    """

    version: int
    job: str
    config: dict[str, Any]


@dataclass(frozen=True)
class NodeGraphSpec:
    """Graph specification (Phase 1 draft).

    Intent:
    - Keep the YAML shape minimal: nodes + edges.
    - Validation and runtime semantics live outside the loader.
    """

    version: int
    nodes: list[NodeSpec]
    edges: list[EdgeSpec]
    config: dict[str, Any]


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return []


def load_graph_spec(path: str | Path) -> GraphSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"graph spec not found: {p}")

    data = OmegaConf.load(p)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"graph spec top-level must be a mapping: {p}")

    version_raw = cont.get("version", 1)
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"graph spec version must be int: {p}") from exc
    if version != 1:
        raise ValueError(f"job graph spec version must be 1: {p} (got {version})")

    job = cont.get("job")
    if not isinstance(job, str) or not job.strip():
        raise ValueError(f"graph spec requires 'job' (module:Name): {p}")

    config = _as_dict(cont.get("config"))
    return GraphSpec(version=version, job=job.strip(), config=config)


def load_node_graph_spec(path: str | Path) -> NodeGraphSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"graph spec not found: {p}")

    data = OmegaConf.load(p)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"graph spec top-level must be a mapping: {p}")

    version_raw = cont.get("version", 2)
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"graph spec version must be int: {p}") from exc
    if version != 2:
        raise ValueError(f"node graph spec version must be 2: {p}")

    nodes_raw = _as_list(cont.get("nodes"))
    edges_raw = _as_list(cont.get("edges"))

    nodes: list[NodeSpec] = []
    for idx, item in enumerate(nodes_raw):
        if not isinstance(item, dict):
            raise ValueError(f"node must be a mapping (index={idx}): {p}")
        node_id = item.get("id", item.get("node_id"))
        plugin = item.get("plugin")
        kind = item.get("kind", "node")
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError(f"node requires non-empty id (index={idx}): {p}")
        if not isinstance(plugin, str) or not plugin.strip():
            raise ValueError(f"node requires non-empty plugin (index={idx}): {p}")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError(f"node kind must be string (index={idx}): {p}")
        config = _as_dict(item.get("config"))
        nodes.append(
            NodeSpec(
                node_id=node_id.strip(),
                plugin=plugin.strip(),
                kind=kind.strip(),
                config=config,
            )
        )

    edges: list[EdgeSpec] = []
    for idx, item in enumerate(edges_raw):
        if not isinstance(item, dict):
            raise ValueError(f"edge must be a mapping (index={idx}): {p}")
        src = item.get("src", item.get("from"))
        dst = item.get("dst", item.get("to"))
        if not isinstance(src, str) or not src.strip():
            raise ValueError(f"edge requires non-empty src/from (index={idx}): {p}")
        if not isinstance(dst, str) or not dst.strip():
            raise ValueError(f"edge requires non-empty dst/to (index={idx}): {p}")
        src_port = item.get("src_port", item.get("from_port"))
        dst_port = item.get("dst_port", item.get("to_port"))
        edges.append(
            EdgeSpec(
                src=src.strip(),
                dst=dst.strip(),
                src_port=str(src_port).strip() if isinstance(src_port, str) and src_port.strip() else None,
                dst_port=str(dst_port).strip() if isinstance(dst_port, str) and dst_port.strip() else None,
            )
        )

    config = _as_dict(cont.get("config"))
    return NodeGraphSpec(version=version, nodes=nodes, edges=edges, config=config)
