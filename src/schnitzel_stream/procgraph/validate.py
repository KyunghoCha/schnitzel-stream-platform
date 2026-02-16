from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from schnitzel_stream.graph.compat import validate_graph_compat
from schnitzel_stream.graph.spec import load_node_graph_spec, peek_graph_version
from schnitzel_stream.graph.validate import validate_graph
from schnitzel_stream.plugins.registry import PluginRegistry
from schnitzel_stream.procgraph.model import ChannelSpec, LinkSpec, ProcessGraphSpec, ProcessSpec
from schnitzel_stream.procgraph.spec import load_process_graph_spec
from schnitzel_stream.project import resolve_project_root

_SQLITE_CHANNEL_KIND = "sqlite_queue"
_SQLITE_SINK_PLUGIN = "schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink"
_SQLITE_SOURCE_PLUGIN = "schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource"
_SQLITE_ACK_PLUGIN = "schnitzel_stream.nodes.durable_sqlite:SqliteQueueAckSink"


class ProcessGraphValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessGraphValidationReport:
    spec_path: str
    process_count: int
    channel_count: int
    link_count: int
    resolved_process_graphs: dict[str, str]
    resolved_channel_paths: dict[str, str]


def _normalize_path(raw: str, *, root: Path) -> Path:
    p = Path(str(raw).strip()).expanduser()
    if not p.is_absolute():
        p = root / p
    return p.resolve()


def _node_paths_by_plugin(process_spec: object, plugin: str, *, field: str) -> list[Path]:
    out: list[Path] = []
    for n in process_spec.nodes:  # type: ignore[attr-defined]
        if str(n.plugin).strip() != plugin:
            continue
        raw = n.config.get(field)
        if not isinstance(raw, str) or not raw.strip():
            continue
        out.append(_normalize_path(raw, root=resolve_project_root()))
    return out


def _load_and_validate_node_graph(
    process: ProcessSpec,
    *,
    root: Path,
    registry: PluginRegistry,
) -> tuple[Path, object]:
    graph_path = _normalize_path(process.graph, root=root)
    try:
        version = peek_graph_version(graph_path)
        if version != 2:
            raise ProcessGraphValidationError(
                f"process={process.process_id} graph must be version=2: {graph_path} (got version={version})"
            )
        spec = load_node_graph_spec(graph_path)
        validate_graph(spec.nodes, spec.edges, allow_cycles=False)
        validate_graph_compat(spec.nodes, spec.edges, transport="inproc", registry=registry)
        return graph_path, spec
    except ProcessGraphValidationError:
        raise
    except Exception as exc:
        raise ProcessGraphValidationError(
            f"process={process.process_id} graph validation failed: {graph_path}: {exc}"
        ) from exc


def _validate_topology(
    spec: ProcessGraphSpec,
) -> tuple[dict[str, ProcessSpec], dict[str, ChannelSpec], dict[str, LinkSpec]]:
    processes = {p.process_id: p for p in spec.processes}
    channels = {c.channel_id: c for c in spec.channels}

    if not processes:
        raise ProcessGraphValidationError("process graph requires at least one process")
    if not channels:
        raise ProcessGraphValidationError("process graph requires at least one channel")
    if not spec.links:
        raise ProcessGraphValidationError("process graph requires at least one link")

    links: dict[str, LinkSpec] = {}
    producer_by_channel: dict[str, set[str]] = {}
    consumer_by_channel: dict[str, set[str]] = {}
    use_count_by_channel: dict[str, int] = {c.channel_id: 0 for c in spec.channels}

    for idx, link in enumerate(spec.links):
        if link.producer not in processes:
            raise ProcessGraphValidationError(f"link[{idx}] unknown producer process: {link.producer}")
        if link.consumer not in processes:
            raise ProcessGraphValidationError(f"link[{idx}] unknown consumer process: {link.consumer}")
        if link.channel not in channels:
            raise ProcessGraphValidationError(f"link[{idx}] unknown channel: {link.channel}")
        if link.producer == link.consumer:
            raise ProcessGraphValidationError(
                f"link[{idx}] producer and consumer must be different: {link.producer}"
            )

        link_id = f"{link.producer}->{link.consumer}@{link.channel}"
        links[link_id] = link

        producer_by_channel.setdefault(link.channel, set()).add(link.producer)
        consumer_by_channel.setdefault(link.channel, set()).add(link.consumer)
        use_count_by_channel[link.channel] = int(use_count_by_channel.get(link.channel, 0)) + 1

    for channel_id, channel in channels.items():
        kind = str(channel.kind).strip()
        if kind != _SQLITE_CHANNEL_KIND:
            raise ProcessGraphValidationError(
                f"channel={channel_id} unsupported kind={kind} (supported: {_SQLITE_CHANNEL_KIND})"
            )
        if use_count_by_channel.get(channel_id, 0) == 0:
            raise ProcessGraphValidationError(f"channel={channel_id} is declared but not linked")

        producers = producer_by_channel.get(channel_id, set())
        consumers = consumer_by_channel.get(channel_id, set())
        if len(producers) != 1 or len(consumers) != 1:
            raise ProcessGraphValidationError(
                "channel cardinality violation: "
                f"channel={channel_id} requires exactly 1 producer and 1 consumer "
                f"(got producers={sorted(producers)} consumers={sorted(consumers)})"
            )
        if int(use_count_by_channel.get(channel_id, 0)) != 1:
            raise ProcessGraphValidationError(
                f"channel={channel_id} must be used by exactly one link in foundation mode"
            )

    return processes, channels, links


def validate_process_graph(
    path: str | Path,
    *,
    registry: PluginRegistry | None = None,
) -> ProcessGraphValidationReport:
    """Validate process-graph spec and SQLite bridge contracts."""

    root = resolve_project_root()
    try:
        spec = load_process_graph_spec(path)
    except Exception as exc:
        raise ProcessGraphValidationError(f"process graph spec load failed: {path}: {exc}") from exc
    processes, channels, links = _validate_topology(spec)

    reg = registry or PluginRegistry()

    loaded_graphs: dict[str, object] = {}
    resolved_graph_paths: dict[str, str] = {}
    for process in processes.values():
        graph_path, node_graph = _load_and_validate_node_graph(process, root=root, registry=reg)
        loaded_graphs[process.process_id] = node_graph
        resolved_graph_paths[process.process_id] = str(graph_path)

    resolved_channel_paths: dict[str, str] = {}
    for channel in channels.values():
        normalized = _normalize_path(channel.path, root=root)
        resolved_channel_paths[channel.channel_id] = str(normalized)

    for link_id, link in links.items():
        channel = channels[link.channel]
        channel_path = _normalize_path(channel.path, root=root)

        prod_graph = loaded_graphs[link.producer]
        cons_graph = loaded_graphs[link.consumer]

        prod_sink_paths = _node_paths_by_plugin(prod_graph, _SQLITE_SINK_PLUGIN, field="path")
        cons_source_paths = _node_paths_by_plugin(cons_graph, _SQLITE_SOURCE_PLUGIN, field="path")
        cons_ack_paths = _node_paths_by_plugin(cons_graph, _SQLITE_ACK_PLUGIN, field="path")

        if channel_path not in prod_sink_paths:
            raise ProcessGraphValidationError(
                "sqlite bridge mismatch: "
                f"link={link_id} producer={link.producer} channel={channel.channel_id} "
                f"requires {_SQLITE_SINK_PLUGIN} with path={channel_path}"
            )
        if channel_path not in cons_source_paths:
            raise ProcessGraphValidationError(
                "sqlite bridge mismatch: "
                f"link={link_id} consumer={link.consumer} channel={channel.channel_id} "
                f"requires {_SQLITE_SOURCE_PLUGIN} with path={channel_path}"
            )
        if channel.require_ack and channel_path not in cons_ack_paths:
            raise ProcessGraphValidationError(
                "sqlite ack contract mismatch: "
                f"link={link_id} consumer={link.consumer} channel={channel.channel_id} "
                f"requires {_SQLITE_ACK_PLUGIN} with path={channel_path}"
            )

    return ProcessGraphValidationReport(
        spec_path=str(_normalize_path(path, root=root)),
        process_count=len(processes),
        channel_count=len(channels),
        link_count=len(links),
        resolved_process_graphs=resolved_graph_paths,
        resolved_channel_paths=resolved_channel_paths,
    )
