# Model Tracking - Design

## English
Design Choice
-------------
Tracking should be implemented inside the *model adapter layer* so that
`RealModelEventBuilder` continues to consume a simple list of detections.
This keeps the pipeline stable and confines tracker dependencies to the vision layer.

Flow
----
1. Model adapter runs detection on each frame.
2. Tracker associates detections across frames and assigns `track_id`.
3. Adapter returns detections with `track_id` set.
4. Builder validates payload and emits events.

Why Adapter-Level Tracking
--------------------------
- Keeps `EventBuilder` API unchanged.
- Allows swapping trackers without touching pipeline code.
- Easier to test in isolation (unit tests for adapter + tracker).

Components
----------
- `IOUTracker` (baseline implemented)
- `ByteTrackTracker` (optional; requires external dependency, fallback to IOU)
- No tracker mode (`TRACKER_TYPE=none`): adapter assigns synthetic `track_id` per detection
- DeepSORT is a future extension (not implemented)

Testing Strategy
----------------
- Unit: IOU tracker assigns stable ids for synthetic sequences.
- Integration: adapter + tracker emits valid events, `track_id` non-null.
- Regression: ensure `track_id` contract remains valid for PERSON.

Status
------
- IOU tracker implemented.
- ByteTrack optional (dependency required; fallback to IOU).
- DeepSORT is a future extension (not implemented).

## 한국어
설계 선택
---------
트래킹은 *모델 어댑터 계층*에서 구현하고, `RealModelEventBuilder`는
단순 detection 리스트만 소비하도록 유지한다.
이렇게 하면 파이프라인 구조를 깨지 않고 비전 레이어에서만 의존성을 관리할 수 있다.

흐름
----
1. 모델 어댑터가 프레임별 detection을 생성한다.
2. 트래커가 연속 프레임에서 detection을 매칭하고 `track_id`를 부여한다.
3. 어댑터는 `track_id`가 포함된 detection을 반환한다.
4. 빌더가 payload 검증 후 이벤트를 emit한다.

왜 어댑터 계층인가
-------------------
- `EventBuilder` API를 바꾸지 않아도 된다.
- 트래커 교체가 파이프라인 코드 변경 없이 가능하다.
- 어댑터+트래커 단위 테스트가 가능하다.

구성 요소
---------
- `IOUTracker` (기준 구현 완료)
- `ByteTrackTracker` (선택, 외부 의존성 필요, 없으면 IOU로 폴백)
- 트래커 비활성 모드(`TRACKER_TYPE=none`): 어댑터가 detection마다 합성 track_id 부여
- DeepSORT는 향후 확장 항목(현재 미구현)

테스트 전략
-----------
- Unit: IOU 트래커에서 안정적인 track_id 부여 확인.
- Integration: 어댑터+트래커에서 `track_id`가 포함된 이벤트 emit 확인.
- Regression: PERSON 계약(track_id 필수) 유지 확인.

상태
-----
- IOU 트래커 구현 완료.
- ByteTrack는 선택 사항(의존성 필요, 없으면 IOU 폴백).
- DeepSORT는 향후 확장 항목(현재 미구현).
