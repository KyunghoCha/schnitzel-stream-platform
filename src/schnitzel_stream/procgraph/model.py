from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessSpec:
    process_id: str
    graph: str


@dataclass(frozen=True)
class ChannelSpec:
    channel_id: str
    kind: str
    path: str
    require_ack: bool = False


@dataclass(frozen=True)
class LinkSpec:
    producer: str
    consumer: str
    channel: str


@dataclass(frozen=True)
class ProcessGraphSpec:
    version: int
    processes: list[ProcessSpec]
    channels: list[ChannelSpec]
    links: list[LinkSpec]

