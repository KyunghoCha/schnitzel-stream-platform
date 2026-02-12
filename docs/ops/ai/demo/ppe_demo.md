# PPE Demo (Non-Production)

## English
Purpose
-------
Provide a demo-only PPE integration using a public PPE model. This is for visualization and pipeline wiring checks only.

Model
-----
- Hansung-Cho PPE YOLOv8 model (demo): `models/yolov8_ppe_hansung.pt`
- Class map (demo): `configs/demo/model_class_map_ppe.yaml`

Run (PPE only)
--------------
```bash
PYTHONPATH=src AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=demo.yolo_ppe_adapter:YOLOPPEAdapter \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
python -m ai.pipeline --source-type file --dry-run --max-events 200 --visualize
```

Run (Person + PPE)
------------------
```bash
PYTHONPATH=src AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter,demo.yolo_ppe_adapter:YOLOPPEAdapter \
ONNX_MODEL_PATH=models/yolov8n.onnx \
ONNX_PROVIDERS=CPUExecutionProvider \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
python -m ai.pipeline --source-type file --dry-run --max-events 200 --visualize
```

Notes
-----
- Demo only. Do not treat PPE detections as production-quality.
- For production, replace with a trained model and update class mapping.

## 한국어
목적
-----
공개 PPE 모델을 이용한 데모 전용 PPE 연동 예시다. 시각화/연동 확인만 목적이다.

모델
-----
- Hansung-Cho PPE YOLOv8 (데모): `models/yolov8_ppe_hansung.pt`
- 클래스 매핑(데모): `configs/demo/model_class_map_ppe.yaml`

실행(PPE만)
------------
```bash
PYTHONPATH=src AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=demo.yolo_ppe_adapter:YOLOPPEAdapter \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
python -m ai.pipeline --source-type file --dry-run --max-events 200 --visualize
```

실행(사람 + PPE)
----------------
```bash
PYTHONPATH=src AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter,demo.yolo_ppe_adapter:YOLOPPEAdapter \
ONNX_MODEL_PATH=models/yolov8n.onnx \
ONNX_PROVIDERS=CPUExecutionProvider \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
python -m ai.pipeline --source-type file --dry-run --max-events 200 --visualize
```

노트
-----
- 데모 전용. PPE 결과를 프로덕션 품질로 간주하지 말 것.
- 프로덕션에서는 학습 모델로 교체하고 클래스 매핑을 갱신한다.
