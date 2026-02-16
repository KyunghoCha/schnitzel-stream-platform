from __future__ import annotations

import textwrap

import pytest

from schnitzel_stream.procgraph.spec import load_process_graph_spec


def _write(path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def test_load_process_graph_spec_parses_v1(tmp_path):
    p = tmp_path / "proc_graph.yaml"
    _write(
        p,
        """
        version: 1
        processes:
          - id: enqueue
            graph: configs/graphs/dev_durable_enqueue_v2.yaml
          - id: drain
            graph: configs/graphs/dev_durable_drain_ack_v2.yaml
        channels:
          - id: q1
            kind: sqlite_queue
            path: outputs/queues/dev_demo.sqlite3
            require_ack: true
        links:
          - producer: enqueue
            consumer: drain
            channel: q1
        """,
    )

    spec = load_process_graph_spec(p)
    assert spec.version == 1
    assert [x.process_id for x in spec.processes] == ["enqueue", "drain"]
    assert [x.channel_id for x in spec.channels] == ["q1"]
    assert [x.producer for x in spec.links] == ["enqueue"]


def test_load_process_graph_spec_rejects_wrong_version(tmp_path):
    p = tmp_path / "proc_graph.yaml"
    _write(
        p,
        """
        version: 2
        processes: []
        channels: []
        links: []
        """,
    )
    with pytest.raises(ValueError, match="unsupported process graph spec version"):
        load_process_graph_spec(p)


def test_load_process_graph_spec_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "proc_graph.yaml"
    _write(
        p,
        """
        version: 1
        processes:
          - id: p1
            graph: g1.yaml
          - id: p1
            graph: g2.yaml
        channels:
          - id: q1
            kind: sqlite_queue
            path: outputs/queues/dev_demo.sqlite3
        links:
          - producer: p1
            consumer: p1
            channel: q1
        """,
    )
    with pytest.raises(ValueError, match="duplicate process id"):
        load_process_graph_spec(p)


def test_load_process_graph_spec_rejects_missing_required_fields(tmp_path):
    p = tmp_path / "proc_graph.yaml"
    _write(
        p,
        """
        version: 1
        processes:
          - id: p1
        channels:
          - id: q1
            kind: sqlite_queue
            path: outputs/queues/dev_demo.sqlite3
        links:
          - producer: p1
            consumer: p2
            channel: q1
        """,
    )
    with pytest.raises(ValueError, match="requires non-empty graph path"):
        load_process_graph_spec(p)

