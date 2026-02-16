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


@pytest.mark.parametrize(
    ("body", "match"),
    [
        (
            """
            version: 2
            processes: []
            channels: []
            links: []
            """,
            "unsupported process graph spec version",
        ),
        (
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
            "duplicate process id",
        ),
        (
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
            "requires non-empty graph path",
        ),
    ],
)
def test_load_process_graph_spec_rejects_invalid_specs(tmp_path, body: str, match: str):
    p = tmp_path / "proc_graph.yaml"
    _write(p, body)
    with pytest.raises(ValueError, match=match):
        load_process_graph_spec(p)
