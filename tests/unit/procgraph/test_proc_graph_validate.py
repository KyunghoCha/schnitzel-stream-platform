from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from schnitzel_stream.procgraph.validate import ProcessGraphValidationError, validate_process_graph


def _write(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def _producer_graph(path: Path, *, queue_path: str) -> None:
    _write(
        path,
        f"""
        version: 2
        nodes:
          - id: src
            kind: source
            plugin: schnitzel_stream.nodes.dev:StaticSource
            config:
              packets:
                - kind: demo
                  source_id: p
                  payload: {{value: 1}}
          - id: queue
            kind: sink
            plugin: schnitzel_stream.nodes.durable_sqlite:SqliteQueueSink
            config:
              path: {queue_path}
              forward: false
        edges:
          - from: src
            to: queue
        config: {{}}
        """,
    )


def _producer_without_queue_sink(path: Path) -> None:
    _write(
        path,
        """
        version: 2
        nodes:
          - id: src
            kind: source
            plugin: schnitzel_stream.nodes.dev:StaticSource
            config:
              packets:
                - kind: demo
                  source_id: p
                  payload: {value: 1}
          - id: out
            kind: sink
            plugin: schnitzel_stream.nodes.dev:PrintSink
            config:
              prefix: "NO_QUEUE "
              forward: false
        edges:
          - from: src
            to: out
        config: {}
        """,
    )


def _consumer_graph(path: Path, *, queue_path: str, include_ack: bool) -> None:
    ack_node = (
        f"""
          - id: ack
            kind: sink
            plugin: schnitzel_stream.nodes.durable_sqlite:SqliteQueueAckSink
            config:
              path: {queue_path}
        """
        if include_ack
        else ""
    )
    ack_edge = (
        """
          - from: out
            to: ack
        """
        if include_ack
        else ""
    )
    _write(
        path,
        f"""
        version: 2
        nodes:
          - id: src
            kind: source
            plugin: schnitzel_stream.nodes.durable_sqlite:SqliteQueueSource
            config:
              path: {queue_path}
              limit: 100
          - id: out
            kind: node
            plugin: schnitzel_stream.nodes.dev:PrintSink
            config:
              prefix: "DRAIN "
              forward: true
{ack_node}
        edges:
          - from: src
            to: out
{ack_edge}
        config: {{}}
        """,
    )


def _proc_spec(path: Path, *, producer_graph: Path, consumer_graph: Path, queue_path: str, require_ack: bool) -> None:
    _write(
        path,
        f"""
        version: 1
        processes:
          - id: enqueue
            graph: {producer_graph}
          - id: drain
            graph: {consumer_graph}
        channels:
          - id: q_main
            kind: sqlite_queue
            path: {queue_path}
            require_ack: {"true" if require_ack else "false"}
        links:
          - producer: enqueue
            consumer: drain
            channel: q_main
        """,
    )


def test_validate_process_graph_accepts_repo_sample():
    root = Path(__file__).resolve().parents[3]
    spec_path = root / "configs" / "process_graphs" / "dev_durable_pair_pg_v1.yaml"
    report = validate_process_graph(spec_path)
    assert report.process_count == 2
    assert report.channel_count == 1
    assert report.link_count == 1


def test_validate_process_graph_rejects_unknown_process_reference(tmp_path: Path):
    queue = "outputs/queues/proc_graph_ref.sqlite3"
    producer = tmp_path / "producer.yaml"
    consumer = tmp_path / "consumer.yaml"
    spec = tmp_path / "proc_graph.yaml"
    _producer_graph(producer, queue_path=queue)
    _consumer_graph(consumer, queue_path=queue, include_ack=True)
    _write(
        spec,
        f"""
        version: 1
        processes:
          - id: enqueue
            graph: {producer}
          - id: drain
            graph: {consumer}
        channels:
          - id: q_main
            kind: sqlite_queue
            path: {queue}
            require_ack: true
        links:
          - producer: unknown
            consumer: drain
            channel: q_main
        """,
    )
    with pytest.raises(ProcessGraphValidationError, match="unknown producer process"):
        validate_process_graph(spec)


def test_validate_process_graph_rejects_channel_cardinality_violation(tmp_path: Path):
    queue = "outputs/queues/proc_graph_cardinality.sqlite3"
    p1 = tmp_path / "producer1.yaml"
    p2 = tmp_path / "producer2.yaml"
    c1 = tmp_path / "consumer.yaml"
    spec = tmp_path / "proc_graph.yaml"
    _producer_graph(p1, queue_path=queue)
    _producer_graph(p2, queue_path=queue)
    _consumer_graph(c1, queue_path=queue, include_ack=True)
    _write(
        spec,
        f"""
        version: 1
        processes:
          - id: p1
            graph: {p1}
          - id: p2
            graph: {p2}
          - id: c1
            graph: {c1}
        channels:
          - id: q_main
            kind: sqlite_queue
            path: {queue}
            require_ack: true
        links:
          - producer: p1
            consumer: c1
            channel: q_main
          - producer: p2
            consumer: c1
            channel: q_main
        """,
    )
    with pytest.raises(ProcessGraphValidationError, match="channel cardinality violation"):
        validate_process_graph(spec)


def test_validate_process_graph_rejects_missing_sqlite_sink(tmp_path: Path):
    queue = "outputs/queues/proc_graph_no_sink.sqlite3"
    producer = tmp_path / "producer.yaml"
    consumer = tmp_path / "consumer.yaml"
    spec = tmp_path / "proc_graph.yaml"
    _producer_without_queue_sink(producer)
    _consumer_graph(consumer, queue_path=queue, include_ack=True)
    _proc_spec(spec, producer_graph=producer, consumer_graph=consumer, queue_path=queue, require_ack=True)
    with pytest.raises(ProcessGraphValidationError, match="SqliteQueueSink"):
        validate_process_graph(spec)


def test_validate_process_graph_rejects_channel_path_mismatch(tmp_path: Path):
    queue_in_graph = "outputs/queues/proc_graph_mismatch_graph.sqlite3"
    queue_in_channel = "outputs/queues/proc_graph_mismatch_channel.sqlite3"
    producer = tmp_path / "producer.yaml"
    consumer = tmp_path / "consumer.yaml"
    spec = tmp_path / "proc_graph.yaml"
    _producer_graph(producer, queue_path=queue_in_graph)
    _consumer_graph(consumer, queue_path=queue_in_graph, include_ack=True)
    _proc_spec(
        spec,
        producer_graph=producer,
        consumer_graph=consumer,
        queue_path=queue_in_channel,
        require_ack=True,
    )
    with pytest.raises(ProcessGraphValidationError, match="sqlite bridge mismatch"):
        validate_process_graph(spec)


def test_validate_process_graph_rejects_missing_ack_when_required(tmp_path: Path):
    queue = "outputs/queues/proc_graph_ack.sqlite3"
    producer = tmp_path / "producer.yaml"
    consumer = tmp_path / "consumer.yaml"
    spec = tmp_path / "proc_graph.yaml"
    _producer_graph(producer, queue_path=queue)
    _consumer_graph(consumer, queue_path=queue, include_ack=False)
    _proc_spec(spec, producer_graph=producer, consumer_graph=consumer, queue_path=queue, require_ack=True)
    with pytest.raises(ProcessGraphValidationError, match="ack contract mismatch"):
        validate_process_graph(spec)

