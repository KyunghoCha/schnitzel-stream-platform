from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from schnitzel_stream.packet import StreamPacket


class Node(Protocol):
    """Packet processing node.

    Contract:
    - Input: one StreamPacket
    - Output: 0..N StreamPackets
    """

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        ...

    def close(self) -> None:
        ...


class SourceNode(Protocol):
    """Packet source node (no inputs)."""

    def run(self) -> Iterable[StreamPacket]:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class RunContext:
    """Runtime context passed to graph jobs."""

    project_root: str
    # CLI args are intentionally opaque to keep the core decoupled.
    args: object

