from __future__ import annotations

import numpy as np
import pytest


class _FakeInput:
    name = "images"
    shape = [1, 3, 640, 640]


class _FakeOutput:
    name = "output0"


class _FakeSession:
    def __init__(self, _model_path: str, providers=None) -> None:
        self.providers = providers or []

    def get_inputs(self):
        return [_FakeInput()]

    def get_outputs(self):
        return [_FakeOutput()]

    def run(self, _output_names, _feeds):
        # [cx, cy, w, h, class0_score, class1_score]
        # Two overlapping detections where the second one has higher score
        # and a different class id.
        out = np.array(
            [
                [50.0, 50.0, 80.0, 80.0, 0.60, 0.10],
                [50.0, 50.0, 60.0, 60.0, 0.10, 0.90],
                [5.0, 5.0, 2.0, 2.0, 0.01, 0.01],
                [5.0, 5.0, 2.0, 2.0, 0.01, 0.01],
                [5.0, 5.0, 2.0, 2.0, 0.01, 0.01],
                [5.0, 5.0, 2.0, 2.0, 0.01, 0.01],
            ],
            dtype=np.float32,
        )
        return [out]


def test_onnx_adapter_keeps_class_id_aligned_after_nms(monkeypatch, tmp_path):
    pytest.importorskip("onnxruntime", exc_type=ImportError)

    from ai.vision.adapters import onnx_adapter as onnx_mod
    from ai.vision.adapters.onnx_adapter import ONNXAdapterConfig

    monkeypatch.setattr(onnx_mod.ort, "InferenceSession", _FakeSession)

    class_map = tmp_path / "class_map.yaml"
    class_map.write_text(
        "\n".join(
            [
                "class_map:",
                "  - class_id: 0",
                "    event_type: ZONE_INTRUSION",
                "    object_type: PERSON",
                "    severity: LOW",
                "  - class_id: 1",
                "    event_type: FIRE_DETECTED",
                "    object_type: FIRE",
                "    severity: HIGH",
            ]
        ),
        encoding="utf-8",
    )

    cfg = ONNXAdapterConfig(
        model_path="dummy.onnx",
        providers=["CPUExecutionProvider"],
        conf_threshold=0.25,
        iou_threshold=0.45,
        tracker_type="none",
        class_map_path=str(class_map),
    )

    adapter = onnx_mod.ONNXYOLOAdapter(config=cfg)
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    out = adapter.infer(frame)

    assert len(out) == 1
    assert out[0]["event_type"] == "FIRE_DETECTED"
    assert out[0]["object_type"] == "FIRE"
