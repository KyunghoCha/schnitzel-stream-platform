from __future__ import annotations

"""
Robotics pack nodes.

Prefer plugin paths under:
- `schnitzel_stream.packs.robotics.nodes:PersonFollowCmdVelNode`
- `schnitzel_stream.packs.robotics.nodes:Ros2CmdVelSink`
"""

from schnitzel_stream.packs.robotics.nodes.person_follow import PersonFollowCmdVelNode, Ros2CmdVelSink

__all__ = [
    "PersonFollowCmdVelNode",
    "Ros2CmdVelSink",
]

