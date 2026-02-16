from __future__ import annotations

from schnitzel_stream.procgraph.model import ChannelSpec, LinkSpec, ProcessGraphSpec, ProcessSpec
from schnitzel_stream.procgraph.spec import load_process_graph_spec

__all__ = [
    "ProcessSpec",
    "ChannelSpec",
    "LinkSpec",
    "ProcessGraphSpec",
    "load_process_graph_spec",
]

