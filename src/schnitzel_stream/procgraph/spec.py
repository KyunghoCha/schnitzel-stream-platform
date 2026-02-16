from __future__ import annotations

from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from schnitzel_stream.procgraph.model import ChannelSpec, LinkSpec, ProcessGraphSpec, ProcessSpec

_SUPPORTED_PROCESS_GRAPH_VERSIONS = (1,)


def _as_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return list(raw)
    return []


def _as_mapping(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _load_yaml_mapping(path: str | Path) -> tuple[Path, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"process graph spec not found: {p}")

    data = OmegaConf.load(p)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"process graph spec top-level must be a mapping: {p}")
    return p, cont


def load_process_graph_spec(path: str | Path) -> ProcessGraphSpec:
    """Load `version: 1` process-graph specification."""

    p, cont = _load_yaml_mapping(path)

    version_raw = cont.get("version")
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"process graph version must be int: {p}") from exc
    if version != 1:
        raise ValueError(
            f"unsupported process graph spec version: {version} "
            f"(supported: {_SUPPORTED_PROCESS_GRAPH_VERSIONS}): {p}"
        )

    processes_raw = _as_list(cont.get("processes"))
    channels_raw = _as_list(cont.get("channels"))
    links_raw = _as_list(cont.get("links"))

    processes: list[ProcessSpec] = []
    seen_process_ids: set[str] = set()
    for idx, item in enumerate(processes_raw):
        if not isinstance(item, dict):
            raise ValueError(f"process item must be a mapping (index={idx}): {p}")
        proc_id = item.get("id", item.get("process_id"))
        graph = item.get("graph")
        if not isinstance(proc_id, str) or not proc_id.strip():
            raise ValueError(f"process requires non-empty id (index={idx}): {p}")
        if not isinstance(graph, str) or not graph.strip():
            raise ValueError(f"process requires non-empty graph path (index={idx}): {p}")
        norm_id = proc_id.strip()
        if norm_id in seen_process_ids:
            raise ValueError(f"duplicate process id: {norm_id} ({p})")
        seen_process_ids.add(norm_id)
        processes.append(ProcessSpec(process_id=norm_id, graph=graph.strip()))

    channels: list[ChannelSpec] = []
    seen_channel_ids: set[str] = set()
    for idx, item in enumerate(channels_raw):
        if not isinstance(item, dict):
            raise ValueError(f"channel item must be a mapping (index={idx}): {p}")
        ch_id = item.get("id", item.get("channel_id"))
        kind = item.get("kind")
        ch_path = item.get("path")
        require_ack = item.get("require_ack", False)
        if not isinstance(ch_id, str) or not ch_id.strip():
            raise ValueError(f"channel requires non-empty id (index={idx}): {p}")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError(f"channel requires non-empty kind (index={idx}): {p}")
        if not isinstance(ch_path, str) or not ch_path.strip():
            raise ValueError(f"channel requires non-empty path (index={idx}): {p}")
        if not isinstance(require_ack, bool):
            raise ValueError(f"channel require_ack must be bool (index={idx}): {p}")
        norm_id = ch_id.strip()
        if norm_id in seen_channel_ids:
            raise ValueError(f"duplicate channel id: {norm_id} ({p})")
        seen_channel_ids.add(norm_id)
        channels.append(
            ChannelSpec(
                channel_id=norm_id,
                kind=kind.strip(),
                path=ch_path.strip(),
                require_ack=require_ack,
            )
        )

    links: list[LinkSpec] = []
    seen_links: set[tuple[str, str, str]] = set()
    for idx, item in enumerate(links_raw):
        if not isinstance(item, dict):
            raise ValueError(f"link item must be a mapping (index={idx}): {p}")
        producer = item.get("producer")
        consumer = item.get("consumer")
        channel = item.get("channel")
        if not isinstance(producer, str) or not producer.strip():
            raise ValueError(f"link requires non-empty producer (index={idx}): {p}")
        if not isinstance(consumer, str) or not consumer.strip():
            raise ValueError(f"link requires non-empty consumer (index={idx}): {p}")
        if not isinstance(channel, str) or not channel.strip():
            raise ValueError(f"link requires non-empty channel (index={idx}): {p}")
        key = (producer.strip(), consumer.strip(), channel.strip())
        if key in seen_links:
            raise ValueError(
                "duplicate link tuple (producer, consumer, channel): "
                f"{key[0]} -> {key[1]} via {key[2]} ({p})"
            )
        seen_links.add(key)
        links.append(LinkSpec(producer=key[0], consumer=key[1], channel=key[2]))

    # Intent: parsing stage is strict about shape but intentionally does not enforce
    # topology/bridge semantics; those are handled by the process-graph validator.
    _ = _as_mapping(cont.get("config"))

    return ProcessGraphSpec(
        version=version,
        processes=processes,
        channels=channels,
        links=links,
    )

