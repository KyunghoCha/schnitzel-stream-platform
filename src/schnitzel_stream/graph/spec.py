from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from schnitzel_stream.graph.model import EdgeSpec, NodeSpec

_SUPPORTED_GRAPH_VERSIONS = (2,)


@dataclass(frozen=True)
class NodeGraphSpec:
    """Node graph specification."""

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


def _load_yaml_mapping(path: str | Path) -> tuple[Path, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"graph spec not found: {p}")

    data = OmegaConf.load(p)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"graph spec top-level must be a mapping: {p}")
    return p, cont


def peek_graph_version(path: str | Path) -> int:
    """Read only the graph version from YAML.

    Intent:
    - Keep version dispatch centralized.
    - Legacy v1(job) specs are intentionally rejected.
    """
    p, cont = _load_yaml_mapping(path)

    version_raw = cont.get("version")
    if version_raw is None:
        has_job = "job" in cont
        has_nodes = "nodes" in cont
        has_edges = "edges" in cont
        if has_job:
            # Intent: fail fast with a migration hint instead of silently treating v1 as default.
            raise ValueError(
                f"legacy v1 job graph is no longer supported: {p}. "
                "Migrate to v2 node graph (nodes/edges).",
            )
        if has_nodes or has_edges:
            return 2
        raise ValueError(f"graph spec must define version=2 or nodes/edges: {p}")

    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"graph spec version must be int: {p}") from exc
    if version != 2:
        raise ValueError(
            f"unsupported graph spec version: {version} (supported: {_SUPPORTED_GRAPH_VERSIONS}); "
            "legacy v1(job) is removed.",
        )
    return version


def load_node_graph_spec(path: str | Path) -> NodeGraphSpec:
    p, cont = _load_yaml_mapping(path)

    version_raw = cont.get("version", 2)
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"graph spec version must be int: {p}") from exc
    if version != 2:
        raise ValueError(f"node graph spec version must be 2 (v1 removed): {p}")

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
        if ":" not in plugin:
            raise ValueError(f"node plugin must be in form 'module:Name' (index={idx}): {p}")
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
