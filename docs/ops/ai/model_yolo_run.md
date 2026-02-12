# YOLO Baseline Integration (Runbook)

## English

Purpose
-------

Define a minimal, stable path to run a pretrained YOLO model with the current pipeline
before custom training. This is a **baseline** for end-to-end validation.

Scope
-----

1. Pretrained YOLO only (no custom training in this phase).
2. Model adapter implements `ModelAdapter` in `src/ai/pipeline/model_adapter.py`.
3. Output must conform to `docs/specs/model_interface.md` and `docs/contracts/protocol.md`.

Constraints
-----------

1. Protocol v0.2 includes `PERSON`, `FIRE`, `SMOKE` plus PPE/POSTURE/HAZARD (draft).
2. Classes beyond this list require a protocol update.
3. Hardware (GPU/Jetson/CPU) is not fixed; FPS/latency targets are TBD.

Recommended Adapter Layout
--------------------------

1. Create `src/ai/vision/adapters/yolo_adapter.py`.
2. Implement `ModelAdapter.infer(frame)` and return detection dict(s).
3. Keep model-specific preprocessing inside the adapter, not in pipeline core.

Detection Mapping Rules
-----------------------

1. Map model class names to `event_type`, `object_type`, `severity`.
2. For PERSON: use `event_type=ZONE_INTRUSION`, `object_type=PERSON`.
3. For FIRE/SMOKE: use `event_type=FIRE_DETECTED` or `SMOKE_DETECTED`.
4. Unknown classes must be dropped or mapped explicitly.
5. Class mapping file (draft): `configs/model_class_map.yaml`.
   - This file is the **project SSOT** for class_id → event mapping.
   - Update after dataset labels are finalized.

Multi-Adapter Merge Policy (current)
------------------------------------

- When `AI_MODEL_ADAPTER` has multiple adapters (comma-separated),
  the pipeline uses `CompositeModelAdapter`.
- Merge rule: **concatenate detections in adapter order**.
- If one adapter fails, its detections are skipped; others continue.
- No cross-model fusion or dedup is applied by default.
  - Use rules/dedup if needed.

Runtime Baseline (example)
--------------------------

1. Install a pretrained YOLO runtime (e.g., Ultralytics or ONNX Runtime).
2. Load the model in the adapter and run inference on each frame.
3. Convert detections to the payload format and return a list.

PT -> ONNX Export (optional)
----------------------------

1. `pip install ultralytics onnx onnxscript`
2. Export command:

```bash
python - <<'PY'
from ultralytics import YOLO
YOLO('models/yolov8n.pt').export(format='onnx', opset=11, simplify=False, dynamic=False)
PY
```

1. Use `models/yolov8n.onnx` as `ONNX_MODEL_PATH`.

Environment Variables
---------------------

1. `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter`
2. `YOLO_MODEL_PATH=/path/to/model.pt`
3. `YOLO_CONF=0.25`
4. YOLO device: `YOLO_DEVICE=auto` (auto -> GPU if available, else CPU)
5. Multiple adapters: `AI_MODEL_ADAPTER=a:AdapterA,b:AdapterB`
6. Tracker (baseline): `TRACKER_TYPE=iou`
7. Tracker options (baseline): `TRACKER_MAX_AGE=30`, `TRACKER_MIN_HITS=1`, `TRACKER_IOU=0.3`
   - Baseline only. Retune after model/data are fixed.
8. Tracker (optional): `TRACKER_TYPE=bytetrack` (requires extra deps; falls back to IOU if missing)
9. Class mapping (optional): `MODEL_CLASS_MAP_PATH=configs/model_class_map.yaml`
10. PPE model path: `YOLO_PPE_MODEL_PATH=/path/to/ppe_model.pt`
11. PPE model conf: `YOLO_PPE_CONF=0.25`
12. PPE class mapping: `MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml`
13. ONNX option: `AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter`
14. ONNX option: `ONNX_MODEL_PATH=/path/to/model.onnx`
15. ONNX option: `ONNX_CONF=0.25`
16. ONNX option: `ONNX_IOU=0.45`
17. ONNX option: `ONNX_PROVIDERS=CUDAExecutionProvider,CPUExecutionProvider`

PPE Demo (Optional)
-------------------
>
> Demo-only. PPE labels vary by model. Update `MODEL_CLASS_MAP_PATH_PPE` to match your taxonomy.
> The demo class map in `configs/demo/model_class_map_ppe.yaml` matches the Hansung-Cho PPE model class ids.

```bash
AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=demo.yolo_ppe_adapter:YOLOPPEAdapter \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
PYTHONPATH=src python -m ai.pipeline --source-type file --dry-run --max-events 3 --visualize
```

Multi-adapter Demo (Person + PPE)
---------------------------------
>
> Person via ONNX, PPE via YOLO(pt). Uses separate class maps.

```bash
AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter,demo.yolo_ppe_adapter:YOLOPPEAdapter \
ONNX_MODEL_PATH=models/yolov8n.onnx \
ONNX_PROVIDERS=CPUExecutionProvider \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
PYTHONPATH=src python -m ai.pipeline --source-type file --dry-run --max-events 3 --visualize
```

Validation Checklist
--------------------

1. Pipeline runs with `model.mode=real`.
2. At least one detection emits valid events.
3. Zone evaluation still works (uses `bbox` + `event_type`).
4. Snapshot path is set only when snapshot saving is enabled.
5. Optional: `--visualize` shows debug bounding boxes.
6. When using multiple adapters, confirm adapter order is reflected in merged output.

Notes
-----

1. Start with a single class (PERSON) to validate the flow.
2. If FPS is low, reduce input resolution or use a smaller YOLO model.
3. Multiple cameras should use one process per camera (current design).

Local GPU Validation (Reference)
--------------------------------

This is a **local-only** record for reproducibility. Different machines may need reinstallation.
See `docs/ops/ai/README.md` for the verified combo and quick checks.

Dependencies (optional)
-----------------------

- Use `requirements-model.txt` for model runtime deps:
  - `ultralytics`, `onnxruntime`, `onnx`, `onnxscript`

## 한국어

목적
-----

사전학습 YOLO 모델을 현재 파이프라인에 붙여 **최소 E2E 검증**을 수행하는 기준 절차를 정의한다.

범위
----

1. 사전학습 YOLO만 사용(커스텀 학습은 후속 단계).
2. 모델 어댑터는 `src/ai/pipeline/model_adapter.py`의 `ModelAdapter`를 구현.
3. 출력은 `docs/specs/model_interface.md`와 `docs/contracts/protocol.md`를 준수.

제약
----

1. 프로토콜 v0.2는 `PERSON`, `FIRE`, `SMOKE` + PPE/POSTURE/HAZARD(초안)를 포함.
2. PPE/자세/위험 클래스는 프로토콜 v0.2에 반영되어 있음(초안).
   그 외 추가 클래스는 프로토콜 업데이트가 선행되어야 함.
3. 하드웨어(GPU/Jetson/CPU)와 FPS/지연 목표는 미정.

권장 어댑터 구성
---------------

1. `src/ai/vision/adapters/yolo_adapter.py` 생성.
2. `ModelAdapter.infer(frame)` 구현 후 detection dict 리스트 반환.
3. 전처리/후처리는 파이프라인이 아닌 어댑터에 둔다.

탐지 매핑 규칙
-------------

1. 모델 클래스명을 `event_type`, `object_type`, `severity`로 매핑.
2. PERSON: `event_type=ZONE_INTRUSION`, `object_type=PERSON`.
3. FIRE/SMOKE: `event_type=FIRE_DETECTED` 또는 `SMOKE_DETECTED`.
4. 정의되지 않은 클래스는 드롭하거나 명시적으로 매핑.
5. 클래스 매핑 파일(초안): `configs/model_class_map.yaml`.
   - class_id → 이벤트 매핑의 **프로젝트 SSOT**.
   - 데이터셋 라벨 확정 후 업데이트 필요.

멀티 어댑터 병합 정책(현재)
---------------------------

- `AI_MODEL_ADAPTER`에 여러 어댑터를 지정하면 `CompositeModelAdapter` 사용.
- 병합 규칙: **어댑터 순서대로 detection을 단순 합산**.
- 한 어댑터 실패는 다른 어댑터를 막지 않음(실패 어댑터 출력 스킵).
- 기본으로 교차 모델 융합/중복 제거는 하지 않음.
  - 필요 시 rules/dedup로 처리.

실행 기준(예시)
--------------

1. 사전학습 YOLO 런타임 설치(예: Ultralytics, ONNX Runtime).
2. 어댑터에서 모델 로드 후 프레임 추론.
3. detection을 페이로드 형식으로 변환 후 리스트 반환.

PT -> ONNX 변환(선택)
---------------------

1. `pip install ultralytics onnx onnxscript`
2. 변환 명령:

```bash
python - <<'PY'
from ultralytics import YOLO
YOLO('models/yolov8n.pt').export(format='onnx', opset=11, simplify=False, dynamic=False)
PY
```

1. `models/yolov8n.onnx`를 `ONNX_MODEL_PATH`로 사용.

환경 변수
---------

1. `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter`
2. `YOLO_MODEL_PATH=/path/to/model.pt`
3. `YOLO_CONF=0.25`
4. YOLO 디바이스: `YOLO_DEVICE=auto` (auto -> GPU 가능 시 GPU, 아니면 CPU)
5. 복수 어댑터: `AI_MODEL_ADAPTER=a:AdapterA,b:AdapterB`
6. 트래커(기준): `TRACKER_TYPE=iou`
7. 트래커 옵션(기준값): `TRACKER_MAX_AGE=30`, `TRACKER_MIN_HITS=1`, `TRACKER_IOU=0.3`
   - 기준값만 제공. 실제 모델/데이터 확정 후 재튜닝 필요.
8. 트래커(선택): `TRACKER_TYPE=bytetrack` (추가 의존성 필요, 없으면 IOU 폴백)
9. 클래스 매핑(선택): `MODEL_CLASS_MAP_PATH=configs/model_class_map.yaml`
10. PPE 모델 경로: `YOLO_PPE_MODEL_PATH=/path/to/ppe_model.pt`
11. PPE 모델 임계값: `YOLO_PPE_CONF=0.25`
12. PPE 클래스 매핑: `MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml`
13. ONNX 옵션: `AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter`
14. ONNX 옵션: `ONNX_MODEL_PATH=/path/to/model.onnx`
15. ONNX 옵션: `ONNX_CONF=0.25`
16. ONNX 옵션: `ONNX_IOU=0.45`
17. ONNX 옵션: `ONNX_PROVIDERS=CUDAExecutionProvider,CPUExecutionProvider`

PPE 데모(선택)
--------------
>
> 데모 전용. PPE 라벨은 모델마다 다르므로 `MODEL_CLASS_MAP_PATH_PPE`를 맞춰야 한다.
> `configs/demo/model_class_map_ppe.yaml`은 Hansung-Cho PPE 모델에 맞춘 예시다.

```bash
AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=demo.yolo_ppe_adapter:YOLOPPEAdapter \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
PYTHONPATH=src:. python -m ai.pipeline --source-type file --dry-run --max-events 3 --visualize
```

멀티 어댑터 데모(사람 + PPE)
----------------------------
>
> 사람은 ONNX, PPE는 YOLO(pt)로 실행. 클래스 매핑을 분리해서 사용.

```bash
AI_MODEL_MODE=real \
AI_MODEL_ADAPTER=ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter,demo.yolo_ppe_adapter:YOLOPPEAdapter \
ONNX_MODEL_PATH=models/yolov8n.onnx \
ONNX_PROVIDERS=CPUExecutionProvider \
YOLO_PPE_MODEL_PATH=models/yolov8_ppe_hansung.pt \
MODEL_CLASS_MAP_PATH_PPE=configs/demo/model_class_map_ppe.yaml \
PYTHONPATH=src:. python -m ai.pipeline --source-type file --dry-run --max-events 3 --visualize
```

검증 체크리스트
--------------

1. `model.mode=real`로 파이프라인이 정상 실행되는지 확인.
2. 최소 1건 이상의 이벤트가 정상 emit 되는지 확인.
3. zone 평가가 정상 동작하는지 확인(`bbox` + `event_type`).
4. 스냅샷은 기능 활성화 시에만 `snapshot_path`가 채워지는지 확인.
5. 선택: `--visualize`로 bbox 디버그 창 확인.
6. 멀티 어댑터 사용 시, 어댑터 순서가 결과에 반영되는지 확인.

노트
----

1. 처음에는 PERSON 단일 클래스로 흐름 검증부터 한다.
2. FPS가 낮으면 해상도를 낮추거나 경량 YOLO 모델을 사용.
3. 멀티카메라는 카메라 1대당 프로세스 1개가 기본 구조.

로컬 GPU 검증 기록(참고)
-------------------------

**로컬 환경 의존** 기록이며, 다른 머신에서는 재설치가 필요할 수 있다.
검증 조합/확인 명령은 `docs/ops/ai/README.md`를 참고.

의존성(선택)
-----------

- 모델 런타임 의존성은 `requirements-model.txt`로 관리한다:
  - `ultralytics`, `onnxruntime`, `onnx`, `onnxscript`
