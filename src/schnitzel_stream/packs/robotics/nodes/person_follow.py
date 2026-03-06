from __future__ import annotations

"""
Person follow robotics nodes.

Intent:
- Convert frame + detection payloads into simple cmd_vel packets.
- Bridge cmd_vel packets to ROS2 `/cmd_vel` with optional dependencies.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import importlib
from typing import Any, Iterable

from schnitzel_stream.packet import StreamPacket


def _as_float(v: Any, *, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _as_int(v: Any, *, default: int) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _as_bool(v: Any, *, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return bool(default)
    if isinstance(v, (int, float)):
        return bool(v)
    text = str(v).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "f", "no", "n", "off", ""}:
        return False
    return bool(default)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(float(lo), min(float(hi), float(v)))


def _parse_int_list(raw: Any, *, fallback: list[int]) -> list[int]:
    if raw is None:
        return list(fallback)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return list(fallback)
        out: list[int] = []
        for part in text.split(","):
            token = part.strip()
            if not token:
                continue
            out.append(int(token))
        return out or list(fallback)
    if isinstance(raw, (list, tuple, set)):
        out = [int(x) for x in raw]
        return out or list(fallback)
    return list(fallback)


def _parse_str_list(raw: Any, *, fallback: list[str]) -> list[str]:
    if raw is None:
        return [str(x) for x in fallback]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return [str(x) for x in fallback]
        out = [p.strip() for p in text.split(",") if p.strip()]
        return out or [str(x) for x in fallback]
    if isinstance(raw, (list, tuple, set)):
        out = [str(x).strip() for x in raw if str(x).strip()]
        return out or [str(x) for x in fallback]
    return [str(x) for x in fallback]


def _bbox_from_detection(det: Mapping[str, Any]) -> tuple[int, int, int, int] | None:
    bbox = det.get("bbox")
    if not isinstance(bbox, Mapping):
        return None
    try:
        x1 = int(round(float(bbox.get("x1"))))
        y1 = int(round(float(bbox.get("y1"))))
        x2 = int(round(float(bbox.get("x2"))))
        y2 = int(round(float(bbox.get("y2"))))
    except Exception:
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def _frame_size(payload: Mapping[str, Any]) -> tuple[int, int] | None:
    frame = payload.get("frame")
    shape = getattr(frame, "shape", None)
    if isinstance(shape, (list, tuple)) and len(shape) >= 2:
        try:
            h = int(shape[0])
            w = int(shape[1])
            if w > 0 and h > 0:
                return (w, h)
        except Exception:
            pass

    for wk, hk in (("frame_width", "frame_height"), ("width", "height")):
        if wk in payload and hk in payload:
            w = _as_int(payload.get(wk), default=0)
            h = _as_int(payload.get(hk), default=0)
            if w > 0 and h > 0:
                return (w, h)
    return None


@dataclass
class PersonFollowCmdVelNode:
    """Generate cmd_vel packets from YOLO-style frame detections.

    Input packet:
    - kind: frame
    - payload.frame: np.ndarray-like (optional if width/height are provided)
    - payload.detections: list[{bbox, class_id/class_name, confidence}] (optional)

    Output packet:
    - kind: cmd_vel
    - payload: {linear_x, angular_z, target_found, ...}

    Config:
    - output_kind: str (default: "cmd_vel")
    - source_id: str (optional; default: packet.source_id)
    - person_class_ids: list[int] | "0,1" (default: [0])
    - person_class_names: list[str] | "person" (default: ["person"])
    - min_confidence: float (default: 0.35)
    - target_select: "largest" | "center" (default: "largest")
    - desired_height_ratio: float (default: 0.35)
    - height_ratio_tolerance: float (default: 0.05)
    - linear_kp: float (default: 0.8)
    - angular_kp: float (default: 1.2)
    - max_linear: float (default: 0.18)
    - min_linear: float (default: 0.0)
    - max_angular: float (default: 1.2)
    - center_error_for_linear: float (default: 0.25)
    - allow_reverse: bool (default: false)
    - default_frame_width: int (default: 640)
    - default_frame_height: int (default: 480)
    """

    INPUT_KINDS = {"frame"}
    OUTPUT_KINDS = {"cmd_vel"}
    INPUT_PROFILE = "inproc_any"
    OUTPUT_PROFILE = "inproc_any"

    node_id: str
    output_kind: str
    output_source_id: str | None
    person_class_ids: set[int]
    person_class_names: set[str]
    min_confidence: float
    target_select: str
    desired_height_ratio: float
    height_ratio_tolerance: float
    linear_kp: float
    angular_kp: float
    max_linear: float
    min_linear: float
    max_angular: float
    center_error_for_linear: float
    allow_reverse: bool
    default_frame_width: int
    default_frame_height: int
    emitted_total: int = 0
    found_total: int = 0
    stopped_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})

        self.node_id = str(node_id or "person_follow_cmd")
        self.output_kind = str(cfg.get("output_kind", "cmd_vel")).strip() or "cmd_vel"
        src_raw = str(cfg.get("source_id", "")).strip()
        self.output_source_id = src_raw if src_raw else None

        cls_ids = _parse_int_list(cfg.get("person_class_ids"), fallback=[0])
        cls_names = _parse_str_list(cfg.get("person_class_names"), fallback=["person"])
        self.person_class_ids = {int(x) for x in cls_ids}
        self.person_class_names = {str(x).strip().lower() for x in cls_names if str(x).strip()}

        self.min_confidence = max(0.0, min(1.0, _as_float(cfg.get("min_confidence", 0.35), default=0.35)))
        self.target_select = str(cfg.get("target_select", "largest")).strip().lower() or "largest"
        if self.target_select not in {"largest", "center"}:
            self.target_select = "largest"

        self.desired_height_ratio = max(
            0.01,
            min(0.99, _as_float(cfg.get("desired_height_ratio", 0.35), default=0.35)),
        )
        self.height_ratio_tolerance = max(
            0.0,
            min(0.5, _as_float(cfg.get("height_ratio_tolerance", 0.05), default=0.05)),
        )

        self.linear_kp = max(0.0, _as_float(cfg.get("linear_kp", 0.8), default=0.8))
        self.angular_kp = max(0.0, _as_float(cfg.get("angular_kp", 1.2), default=1.2))
        self.max_linear = max(0.0, _as_float(cfg.get("max_linear", 0.18), default=0.18))
        self.min_linear = max(0.0, _as_float(cfg.get("min_linear", 0.0), default=0.0))
        self.max_angular = max(0.0, _as_float(cfg.get("max_angular", 1.2), default=1.2))
        self.center_error_for_linear = max(
            0.0,
            min(1.0, _as_float(cfg.get("center_error_for_linear", 0.25), default=0.25)),
        )
        self.allow_reverse = _as_bool(cfg.get("allow_reverse", False), default=False)

        self.default_frame_width = max(1, _as_int(cfg.get("default_frame_width", 640), default=640))
        self.default_frame_height = max(1, _as_int(cfg.get("default_frame_height", 480), default=480))

        self.emitted_total = 0
        self.found_total = 0
        self.stopped_total = 0

    def _is_person_detection(self, det: Mapping[str, Any]) -> bool:
        conf = _as_float(det.get("confidence", 0.0), default=0.0)
        if conf < self.min_confidence:
            return False

        id_ok = False
        class_id_raw = det.get("class_id", None)
        if class_id_raw is not None:
            try:
                id_ok = int(class_id_raw) in self.person_class_ids
            except Exception:
                id_ok = False

        name_raw = str(det.get("class_name", det.get("label", ""))).strip().lower()
        name_ok = bool(name_raw) and name_raw in self.person_class_names

        if self.person_class_ids and self.person_class_names:
            return id_ok or name_ok
        if self.person_class_ids:
            return id_ok
        if self.person_class_names:
            return name_ok
        return True

    def _select_target(
        self,
        *,
        candidates: list[tuple[Mapping[str, Any], tuple[int, int, int, int]]],
        frame_w: int,
    ) -> tuple[Mapping[str, Any], tuple[int, int, int, int]]:
        if self.target_select == "center":
            return min(
                candidates,
                key=lambda item: abs((float(item[1][0] + item[1][2]) * 0.5) - (float(frame_w) * 0.5)),
            )
        return max(candidates, key=lambda item: float(item[1][2] - item[1][0]) * float(item[1][3] - item[1][1]))

    def _cmd_packet(
        self,
        *,
        packet: StreamPacket,
        linear_x: float,
        angular_z: float,
        target_found: bool,
        frame_w: int,
        frame_h: int,
        candidate_count: int,
        selected_bbox: tuple[int, int, int, int] | None = None,
        error_x_norm: float = 0.0,
        bbox_height_ratio: float = 0.0,
        confidence: float = 0.0,
    ) -> StreamPacket:
        payload: dict[str, Any] = {
            "linear_x": float(linear_x),
            "angular_z": float(angular_z),
            "target_found": bool(target_found),
            "candidate_count": int(candidate_count),
            "frame_width": int(frame_w),
            "frame_height": int(frame_h),
            "error_x_norm": float(error_x_norm),
            "bbox_height_ratio": float(bbox_height_ratio),
            "target_select": self.target_select,
        }
        if selected_bbox is not None:
            x1, y1, x2, y2 = selected_bbox
            payload["target_bbox"] = {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)}
            payload["target_confidence"] = float(confidence)

        meta = dict(packet.meta)
        meta["target_found"] = bool(target_found)
        meta["candidate_count"] = int(candidate_count)
        source_id = self.output_source_id or str(packet.source_id)
        return StreamPacket.new(kind=self.output_kind, source_id=source_id, payload=payload, ts=packet.ts, meta=meta)

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if not isinstance(packet.payload, Mapping):
            raise TypeError(f"{self.node_id}: expected payload as mapping")
        payload = packet.payload

        wh = _frame_size(payload)
        if wh is None:
            frame_w = int(self.default_frame_width)
            frame_h = int(self.default_frame_height)
        else:
            frame_w, frame_h = int(wh[0]), int(wh[1])

        raw_dets = payload.get("detections", [])
        if not isinstance(raw_dets, list):
            raise TypeError(f"{self.node_id}: expected payload.detections as list")

        candidates: list[tuple[Mapping[str, Any], tuple[int, int, int, int]]] = []
        for raw in raw_dets:
            if not isinstance(raw, Mapping):
                continue
            bbox = _bbox_from_detection(raw)
            if bbox is None:
                continue
            if not self._is_person_detection(raw):
                continue
            candidates.append((raw, bbox))

        if not candidates:
            self.emitted_total += 1
            self.stopped_total += 1
            return [
                self._cmd_packet(
                    packet=packet,
                    linear_x=0.0,
                    angular_z=0.0,
                    target_found=False,
                    frame_w=frame_w,
                    frame_h=frame_h,
                    candidate_count=0,
                )
            ]

        det, bbox = self._select_target(candidates=candidates, frame_w=frame_w)
        x1, y1, x2, y2 = bbox
        center_x = 0.5 * float(x1 + x2)
        err_x_norm = (center_x - (0.5 * float(frame_w))) / max(1.0, 0.5 * float(frame_w))
        err_x_norm = _clamp(err_x_norm, -1.0, 1.0)

        bbox_h = float(y2 - y1)
        bbox_h_ratio = bbox_h / max(1.0, float(frame_h))
        range_err = float(self.desired_height_ratio) - float(bbox_h_ratio)

        if abs(range_err) <= self.height_ratio_tolerance:
            linear_x = 0.0
        else:
            linear_x = float(self.linear_kp) * float(range_err)
        linear_x = _clamp(linear_x, -self.max_linear, self.max_linear)

        if not self.allow_reverse and linear_x < 0.0:
            linear_x = 0.0
        if abs(err_x_norm) > self.center_error_for_linear:
            linear_x = 0.0

        if linear_x > 0.0 and linear_x < self.min_linear:
            linear_x = float(self.min_linear)
        if self.allow_reverse and linear_x < 0.0 and abs(linear_x) < self.min_linear:
            linear_x = -float(self.min_linear)

        angular_z = _clamp(-float(self.angular_kp) * float(err_x_norm), -self.max_angular, self.max_angular)

        self.emitted_total += 1
        self.found_total += 1
        conf = _as_float(det.get("confidence", 0.0), default=0.0)
        return [
            self._cmd_packet(
                packet=packet,
                linear_x=linear_x,
                angular_z=angular_z,
                target_found=True,
                frame_w=frame_w,
                frame_h=frame_h,
                candidate_count=len(candidates),
                selected_bbox=bbox,
                error_x_norm=err_x_norm,
                bbox_height_ratio=bbox_h_ratio,
                confidence=conf,
            )
        ]

    def metrics(self) -> dict[str, int]:
        return {
            "emitted_total": int(self.emitted_total),
            "found_total": int(self.found_total),
            "stopped_total": int(self.stopped_total),
        }

    def close(self) -> None:
        return


def _import_ros2_modules() -> tuple[Any, Any]:
    try:
        rclpy = importlib.import_module("rclpy")
        geom_msg = importlib.import_module("geometry_msgs.msg")
    except Exception as exc:
        raise ImportError("Ros2CmdVelSink requires ROS2 Python packages (rclpy, geometry_msgs)") from exc

    twist_cls = getattr(geom_msg, "Twist", None)
    if twist_cls is None:
        raise ImportError("Ros2CmdVelSink requires geometry_msgs.msg.Twist")
    return rclpy, twist_cls


def _create_ros2_node(*, rclpy: Any, node_name: str) -> Any:
    create_node_fn = getattr(rclpy, "create_node", None)
    if callable(create_node_fn):
        return create_node_fn(str(node_name))
    node_mod = importlib.import_module("rclpy.node")
    node_cls = getattr(node_mod, "Node", None)
    if node_cls is None:
        raise RuntimeError("unable to create ROS2 node: rclpy node API not found")
    return node_cls(str(node_name))


@dataclass
class Ros2CmdVelSink:
    """Publish cmd_vel packets to ROS2.

    Input packet:
    - kind: cmd_vel
    - payload: {linear_x: float, angular_z: float}

    Config:
    - topic: str (default: /cmd_vel)
    - node_name: str (default: schnitzel_cmd_vel_sink)
    - qos_depth: int (default: 10)
    - stop_on_close: bool (default: true)
    - forward: bool (default: false)
    """

    INPUT_KINDS = {"cmd_vel"}
    OUTPUT_KINDS = {"*"}
    INPUT_PROFILE = "inproc_any"
    OUTPUT_PROFILE = "inproc_any"

    node_id: str
    topic: str
    node_name: str
    qos_depth: int
    stop_on_close: bool
    forward: bool
    published_total: int = 0

    def __init__(self, *, node_id: str | None = None, config: dict[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self.node_id = str(node_id or "ros2_cmd_vel_sink")
        self.topic = str(cfg.get("topic", "/cmd_vel")).strip() or "/cmd_vel"
        self.node_name = str(cfg.get("node_name", "schnitzel_cmd_vel_sink")).strip() or "schnitzel_cmd_vel_sink"
        self.qos_depth = max(1, _as_int(cfg.get("qos_depth", 10), default=10))
        self.stop_on_close = _as_bool(cfg.get("stop_on_close", True), default=True)
        self.forward = _as_bool(cfg.get("forward", False), default=False)
        self.published_total = 0

        self._rclpy, self._twist_cls = _import_ros2_modules()

        ok_fn = getattr(self._rclpy, "ok", None)
        is_ok = bool(ok_fn()) if callable(ok_fn) else False
        self._owns_context = False
        if not is_ok:
            init_fn = getattr(self._rclpy, "init", None)
            if not callable(init_fn):
                raise RuntimeError("Ros2CmdVelSink: rclpy.init() is unavailable")
            init_fn(args=None)
            self._owns_context = True

        self._node = _create_ros2_node(rclpy=self._rclpy, node_name=self.node_name)
        self._pub = self._node.create_publisher(self._twist_cls, self.topic, int(self.qos_depth))
        self._closed = False

    def _extract_cmd(self, payload: Mapping[str, Any]) -> tuple[float, float]:
        if "linear_x" in payload or "angular_z" in payload:
            return (
                _as_float(payload.get("linear_x", 0.0), default=0.0),
                _as_float(payload.get("angular_z", 0.0), default=0.0),
            )

        twist_raw = payload.get("twist")
        if isinstance(twist_raw, Mapping):
            linear_raw = twist_raw.get("linear")
            angular_raw = twist_raw.get("angular")
            lx = 0.0
            az = 0.0
            if isinstance(linear_raw, Mapping):
                lx = _as_float(linear_raw.get("x", 0.0), default=0.0)
            if isinstance(angular_raw, Mapping):
                az = _as_float(angular_raw.get("z", 0.0), default=0.0)
            return lx, az

        return 0.0, 0.0

    def _publish(self, linear_x: float, angular_z: float) -> None:
        msg = self._twist_cls()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self._pub.publish(msg)
        self.published_total += 1

    def process(self, packet: StreamPacket) -> Iterable[StreamPacket]:
        if self._closed:
            return []
        if not isinstance(packet.payload, Mapping):
            raise TypeError(f"{self.node_id}: expected payload as mapping")

        linear_x, angular_z = self._extract_cmd(packet.payload)
        self._publish(linear_x, angular_z)
        if self.forward:
            return [packet]
        return []

    def metrics(self) -> dict[str, int]:
        return {"published_total": int(self.published_total)}

    def close(self) -> None:
        if getattr(self, "_closed", True):
            return
        self._closed = True

        if self.stop_on_close:
            try:
                self._publish(0.0, 0.0)
            except Exception:
                pass

        destroy_fn = getattr(self._node, "destroy_node", None)
        if callable(destroy_fn):
            destroy_fn()

        if bool(getattr(self, "_owns_context", False)):
            shutdown_fn = getattr(self._rclpy, "shutdown", None)
            if callable(shutdown_fn):
                shutdown_fn()

