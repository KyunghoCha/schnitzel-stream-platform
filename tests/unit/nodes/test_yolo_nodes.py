from __future__ import annotations

from pathlib import Path

import pytest

import schnitzel_stream.packs.vision.nodes.yolo as yolo_mod
from schnitzel_stream.packs.vision.nodes.yolo import OpenCvBboxDisplaySink, YoloV8DetectorNode
from schnitzel_stream.packet import StreamPacket


def test_yolo_detector_attaches_detection_payload(monkeypatch, tmp_path: Path):
    model_path = tmp_path / "yolov8n.pt"
    model_path.write_bytes(b"fake-model")

    instances: list[object] = []

    class _Box:
        def __init__(self, xyxy, conf, cls_id):
            self.xyxy = [xyxy]
            self.conf = [conf]
            self.cls = [cls_id]

    class _Result:
        def __init__(self):
            self.boxes = [_Box([10, 20, 30, 40], 0.91, 0), _Box([15, 25, 45, 55], 0.77, 2)]
            self.names = {0: "person", 2: "car"}

    class _FakeYOLO:
        def __init__(self, path: str):
            self.path = path
            self.names = {0: "person", 2: "car"}
            self.calls: list[dict[str, object]] = []
            instances.append(self)

        def predict(self, frame, **kwargs):
            self.calls.append(dict(kwargs))
            return [_Result()]

    monkeypatch.setattr(yolo_mod, "_YOLO", _FakeYOLO)

    node = YoloV8DetectorNode(
        config={
            "model_path": str(model_path),
            "conf": 0.3,
            "iou": 0.5,
            "max_det": 10,
            "classes": "0,2",
            "device": "cpu",
        }
    )
    pkt = StreamPacket.new(kind="frame", source_id="cam01", payload={"frame": object(), "frame_idx": 12})

    out = list(node.process(pkt))
    assert len(out) == 1
    assert out[0].kind == "frame"
    assert out[0].payload["frame_idx"] == 12
    assert len(out[0].payload["detections"]) == 2
    assert out[0].payload["detections"][0]["class_name"] == "person"
    assert out[0].payload["detections"][1]["class_id"] == 2
    assert out[0].meta["detection_count"] == 2
    assert out[0].meta["model"] == "yolov8n.pt"

    fake = instances[0]
    assert fake.calls[0]["classes"] == [0, 2]
    assert fake.calls[0]["device"] == "cpu"
    assert node.metrics()["detected_total"] == 2


def test_yolo_detector_requires_ultralytics(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(yolo_mod, "_YOLO", None)
    with pytest.raises(ImportError):
        YoloV8DetectorNode(config={"model_path": str(tmp_path / "yolov8n.pt")})


def test_opencv_bbox_display_sink_draws_boxes(monkeypatch):
    class _FakeCv2:
        FONT_HERSHEY_SIMPLEX = 0
        LINE_AA = 16

        def __init__(self):
            self.rectangles: list[tuple[int, int, int, int]] = []
            self.imshow_calls = 0
            self.destroyed: list[str] = []

        def rectangle(self, _frame, p1, p2, _color, _thickness):
            self.rectangles.append((int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1])))

        def putText(self, *_args, **_kwargs):
            return None

        def imshow(self, _window_name, _frame):
            self.imshow_calls += 1

        def waitKey(self, _ms):
            return -1

        def destroyWindow(self, name):
            self.destroyed.append(str(name))

    class _Frame:
        def copy(self):
            return self

    fake_cv2 = _FakeCv2()
    monkeypatch.setattr(yolo_mod, "cv2", fake_cv2)

    sink = OpenCvBboxDisplaySink(config={"window_name": "test-window", "stop_on_quit_key": True})
    pkt = StreamPacket.new(
        kind="frame",
        source_id="cam01",
        payload={
            "frame": _Frame(),
            "frame_idx": 1,
            "detections": [
                {"bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40}, "class_name": "person", "confidence": 0.9}
            ],
        },
    )

    out = list(sink.process(pkt))
    assert out == []
    assert fake_cv2.imshow_calls == 1
    assert fake_cv2.rectangles == [(10, 20, 30, 40)]

    sink.close()
    assert fake_cv2.destroyed == ["test-window"]


def test_opencv_bbox_display_sink_quit_key_raises_keyboard_interrupt(monkeypatch):
    class _FakeCv2:
        FONT_HERSHEY_SIMPLEX = 0
        LINE_AA = 16

        def rectangle(self, *_args, **_kwargs):
            return None

        def putText(self, *_args, **_kwargs):
            return None

        def imshow(self, *_args, **_kwargs):
            return None

        def waitKey(self, _ms):
            return ord("q")

        def destroyWindow(self, *_args, **_kwargs):
            return None

    class _Frame:
        def copy(self):
            return self

    monkeypatch.setattr(yolo_mod, "cv2", _FakeCv2())

    sink = OpenCvBboxDisplaySink(config={"stop_on_quit_key": True})
    pkt = StreamPacket.new(kind="frame", source_id="cam01", payload={"frame": _Frame(), "frame_idx": 2, "detections": []})
    with pytest.raises(KeyboardInterrupt):
        list(sink.process(pkt))
