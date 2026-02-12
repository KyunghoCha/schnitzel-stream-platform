# Model Interface Specification v0.2

## English

## Purpose

Define the interface between the **AI Model Adapter** and the **Pipeline Core**. This ensures the pipeline can work with any model (YOLO v8/v11, ONNX, etc.) as long as it has a compatible adapter.

## Adapter Interface (Python)

```python
class ModelAdapter(Protocol):
    def infer(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """
        Input: BGR image (OpenCV format)
        Output: List of detection dictionaries
        """
        ...
```

### Detection Dictionary Fields

- `bbox`: `{"x1": int, "y1": int, "x2": int, "y2": int}` (pixel coordinates)
- `confidence`: `float` (0.0 ~ 1.0)
- `track_id`: `int` (optional, but required for PERSISTENT tracking)
- `event_type`: `str` (e.g., "ZONE_INTRUSION", "FIRE_DETECTED")
- `object_type`: `str` (e.g., "PERSON", "FIRE", "SMOKE", "HELMET")
- `severity`: `str` ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")

## Code Mapping

- Adapter Loader: `src/ai/pipeline/model_adapter.py`
- Example Adapter: `src/ai/vision/adapters/yolo_adapter.py`
- Real Builder: `src/ai/pipeline/events.py` -> `RealModelEventBuilder`

---

## 한국어

모델 인터페이스 명세 v0.2
=======================

## 목적

**AI 모델 어댑터(Adapter)**와 **파이프라인 코어(Core)** 간의 인터페이스를 정의함. 이를 통해 YOLO v8/v11, ONNX 등 다양한 모델이 어댑터만 있다면 파이프라인과 연동될 수 있도록 보장함.

## 어댑터 인터페이스 (Python)

```python
class ModelAdapter(Protocol):
    def infer(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """
        입력: BGR 이미지 (OpenCV 포맷)
        출력: 탐지 결과 딕셔너리 리스트
        """
        ...
```

### 탐지 결과 필드 (Detection Dictionary)

- `bbox`: `{"x1": int, "y1": int, "x2": int, "y2": int}` (픽셀 좌표)
- `confidence`: `float` (0.0 ~ 1.0)
- `track_id`: `int` (선택 사항, 단 지속적인 트래킹 시 필수)
- `event_type`: `str` (예: "ZONE_INTRUSION", "FIRE_DETECTED")
- `object_type`: `str` (예: "PERSON", "FIRE", "SMOKE", "HELMET")
- `severity`: `str` ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")

## 코드 매핑

- 어댑터 로더: `src/ai/pipeline/model_adapter.py`
- 어댑터 예시: `src/ai/vision/adapters/yolo_adapter.py`
- 실제 빌더: `src/ai/pipeline/events.py` 내 `RealModelEventBuilder`
