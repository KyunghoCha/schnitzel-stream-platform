# AI Ops

## English
This folder contains AI-model-specific operational documents (training, labeling, validation, and performance).

Files
-----
- `model_yolo_run.md`
- `model_training_plan.md`
- `labeling_guide.md`
- `training_report_template.md`
- `accuracy_validation.md`
- `performance_optimization.md`

Local GPU Validation (Reference)
--------------------------------
This is a **local-only** record for reproducibility. Different machines may need reinstallation.

Verified combo (this workstation):
- Driver: NVIDIA 580.126.09 (CUDA 13.0 reported by driver)
- GPU: NVIDIA TITAN Xp
- `torch==2.2.2+cu118`
- `onnxruntime-gpu==1.17.1`
- `onnx==1.13.1`
- `numpy==1.26.4`
- `protobuf==3.20.3`

Quick checks:
```bash
python - <<'PY'
import torch
print('cuda:', torch.cuda.is_available())
print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')
PY

python - <<'PY'
import onnxruntime as ort
print(ort.__version__)
print(ort.get_available_providers())
PY
```

## 한국어
이 폴더는 AI 모델 관련 운영 문서(학습, 라벨링, 검증, 성능)를 모아둔다.

파일 목록
---------
- `model_yolo_run.md`
- `model_training_plan.md`
- `labeling_guide.md`
- `training_report_template.md`
- `accuracy_validation.md`
- `performance_optimization.md`

로컬 GPU 검증 기록(참고)
-------------------------
**로컬 환경 의존** 기록이며, 다른 머신에서는 재설치가 필요할 수 있다.

검증된 조합(현재 워크스테이션):
- 드라이버: NVIDIA 580.126.09 (드라이버가 CUDA 13.0 표시)
- GPU: NVIDIA TITAN Xp
- `torch==2.2.2+cu118`
- `onnxruntime-gpu==1.17.1`
- `onnx==1.13.1`
- `numpy==1.26.4`
- `protobuf==3.20.3`

간단 확인:
```bash
python - <<'PY'
import torch
print('cuda:', torch.cuda.is_available())
print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')
PY

python - <<'PY'
import onnxruntime as ort
print(ort.__version__)
print(ort.get_available_providers())
PY
```
