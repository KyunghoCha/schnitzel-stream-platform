# Model Tracking - Spec

## English

Behavior
--------

- Input: per-frame detections from model adapter (bbox, confidence, class mapping).
- Output: same detections augmented with a stable `track_id` for PERSON.
- `track_id` is stable across consecutive frames for the same object.
- `track_id` is unique per camera/process (no global uniqueness required).

Rules
-----

- PERSON: `track_id` **required**.
- FIRE/SMOKE: `track_id` optional (can be null).
- If tracker is disabled/unavailable, adapter must emit synthetic `track_id`
  per detection (already supported as fallback).

Config
------

- `TRACKER_TYPE`: `none` | `iou` | `bytetrack` (default: `none`)
- `TRACKER_MAX_AGE`: max frames to keep a track alive (default: 30)
- `TRACKER_MIN_HITS`: min frames before confirming track (default: 1)
- `TRACKER_IOU`: IoU threshold for association (default: 0.3)

Baseline Tuning (Temporary)
---------------------------

- The defaults above are **baseline values** only.
- Final tuning must be done after the real model/data is fixed.
- Record tuned values in `docs/packs/vision/ops/ai/model_yolo_run.md` and update this spec.

Status
------

- IOU tracker implemented (baseline).
- ByteTrack is optional (requires external dependency; fallback to IOU).
- DeepSORT is a future extension (not implemented).

Code Mapping
------------

- Adapter wrapper: `src/ai/pipeline/model_adapter.py`
- Tracker selection: `src/ai/vision/trackers/tracker_factory.py`
- Trackers: `src/ai/vision/trackers/tracker_iou.py`, `src/ai/vision/trackers/tracker_bytetrack.py`
- Builder integration: `src/ai/pipeline/events.py` (RealModelEventBuilder)

## 한국어

동작
----

- 입력: 모델 어댑터의 프레임별 detection 결과(bbox, confidence, class 매핑).
- 출력: 동일 detection에 안정적인 `track_id`를 부여(PERSON 기준).
- 동일 객체에 대해 연속 프레임에서 `track_id`가 유지되어야 한다.
- `track_id`는 카메라/프로세스 단위로만 유일하면 된다.

규칙
----

- PERSON: `track_id` **필수**.
- FIRE/SMOKE: `track_id`는 선택(null 허용).
- 트래커가 비활성/부재인 경우에는 detection마다 합성 `track_id`를 부여한다
  (현재 fallback 지원).

설정
-----

- `TRACKER_TYPE`: `none` | `iou` | `bytetrack` (기본: `none`)
- `TRACKER_MAX_AGE`: track 유지 최대 프레임 (기본: 30)
- `TRACKER_MIN_HITS`: track 확정 최소 프레임 (기본: 1)
- `TRACKER_IOU`: 매칭 IoU 임계값 (기본: 0.3)

기준 튜닝(임시)
-------------

- 위 기본값은 **임시 기준값**이다.
- 실제 모델/데이터가 확정된 뒤 반드시 재튜닝한다.
- 튜닝 결과는 `docs/packs/vision/ops/ai/model_yolo_run.md`에 기록하고 본 문서를 갱신한다.

상태
-----

- IOU 트래커 구현(기준).
- ByteTrack는 외부 의존성 필요(없으면 IOU로 폴백).
- DeepSORT는 향후 확장 항목(현재 미구현).

코드 매핑
---------

- 어댑터 래퍼: `src/ai/pipeline/model_adapter.py`
- 트래커 선택: `src/ai/vision/trackers/tracker_factory.py`
- 트래커 구현: `src/ai/vision/trackers/tracker_iou.py`, `src/ai/vision/trackers/tracker_bytetrack.py`
- 빌더 연동: `src/ai/pipeline/events.py` (RealModelEventBuilder)
