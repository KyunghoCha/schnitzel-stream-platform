from __future__ import annotations

import schnitzel_stream.packs.robotics.nodes.person_follow as follow_mod
from schnitzel_stream.packs.robotics.nodes.person_follow import PersonFollowCmdVelNode, Ros2CmdVelSink
from schnitzel_stream.packet import StreamPacket


class _Frame:
    def __init__(self, *, h: int = 480, w: int = 640) -> None:
        self.shape = (int(h), int(w), 3)


def test_person_follow_generates_forward_command_for_center_target():
    node = PersonFollowCmdVelNode()
    pkt = StreamPacket.new(
        kind="frame",
        source_id="cam01",
        payload={
            "frame": _Frame(h=480, w=640),
            "detections": [
                {
                    "bbox": {"x1": 280, "y1": 180, "x2": 360, "y2": 300},
                    "confidence": 0.92,
                    "class_id": 0,
                    "class_name": "person",
                }
            ],
        },
    )

    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].kind == "cmd_vel"
    assert out[0].payload["target_found"] is True
    assert out[0].payload["linear_x"] > 0.0
    assert abs(out[0].payload["angular_z"]) < 1e-9
    assert node.metrics()["found_total"] == 1


def test_person_follow_stops_when_no_person_target():
    node = PersonFollowCmdVelNode()
    pkt = StreamPacket.new(
        kind="frame",
        source_id="cam01",
        payload={
            "frame": _Frame(h=480, w=640),
            "detections": [
                {
                    "bbox": {"x1": 200, "y1": 180, "x2": 280, "y2": 300},
                    "confidence": 0.95,
                    "class_id": 2,
                    "class_name": "car",
                }
            ],
        },
    )

    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].payload["target_found"] is False
    assert out[0].payload["linear_x"] == 0.0
    assert out[0].payload["angular_z"] == 0.0
    assert node.metrics()["stopped_total"] == 1


def test_person_follow_turns_and_blocks_linear_when_target_is_off_center():
    node = PersonFollowCmdVelNode(config={"center_error_for_linear": 0.2, "allow_reverse": False})
    pkt = StreamPacket.new(
        kind="frame",
        source_id="cam01",
        payload={
            "frame": _Frame(h=480, w=640),
            "detections": [
                {
                    "bbox": {"x1": 500, "y1": 160, "x2": 620, "y2": 300},
                    "confidence": 0.88,
                    "class_id": 0,
                    "class_name": "person",
                }
            ],
        },
    )

    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].payload["target_found"] is True
    assert out[0].payload["linear_x"] == 0.0
    assert out[0].payload["angular_z"] < 0.0


def test_ros2_cmd_vel_sink_publishes_and_stops_on_close(monkeypatch):
    class _Vector3:
        def __init__(self) -> None:
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0

    class _Twist:
        def __init__(self) -> None:
            self.linear = _Vector3()
            self.angular = _Vector3()

    class _Publisher:
        def __init__(self) -> None:
            self.sent: list[tuple[float, float]] = []

        def publish(self, msg) -> None:
            self.sent.append((float(msg.linear.x), float(msg.angular.z)))

    class _Node:
        def __init__(self, name: str) -> None:
            self.name = str(name)
            self.publisher = _Publisher()
            self.destroyed = False

        def create_publisher(self, _msg_type, _topic: str, _depth: int):
            return self.publisher

        def destroy_node(self) -> None:
            self.destroyed = True

    class _FakeRclpy:
        def __init__(self) -> None:
            self._ok = False
            self.init_calls = 0
            self.shutdown_calls = 0
            self.nodes: list[_Node] = []

        def ok(self) -> bool:
            return self._ok

        def init(self, args=None) -> None:
            self._ok = True
            self.init_calls += 1

        def shutdown(self) -> None:
            self._ok = False
            self.shutdown_calls += 1

        def create_node(self, name: str) -> _Node:
            node = _Node(name)
            self.nodes.append(node)
            return node

    fake_rclpy = _FakeRclpy()
    monkeypatch.setattr(follow_mod, "_import_ros2_modules", lambda: (fake_rclpy, _Twist))

    sink = Ros2CmdVelSink(config={"topic": "/cmd_vel", "stop_on_close": True})
    pkt = StreamPacket.new(kind="cmd_vel", source_id="cam01", payload={"linear_x": 0.12, "angular_z": -0.33})
    out = list(sink.process(pkt))
    assert out == []
    assert fake_rclpy.init_calls == 1
    assert fake_rclpy.nodes[0].publisher.sent[0] == (0.12, -0.33)

    sink.close()
    assert fake_rclpy.nodes[0].publisher.sent[-1] == (0.0, 0.0)
    assert fake_rclpy.nodes[0].destroyed is True
    assert fake_rclpy.shutdown_calls == 1

