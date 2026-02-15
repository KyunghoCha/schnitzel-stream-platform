# Model Tracking - Overview

## English
Purpose
-------
Define how tracking (stable `track_id`) should be integrated into the model adapter pipeline.

Scope
-----
- Track IDs for PERSON are required by `docs/packs/vision/event_protocol_v0.2.md`.
- FIRE/SMOKE may omit `track_id`.
- IOU tracker is implemented; ByteTrack is optional (dependency-based).
- DeepSORT is a future extension (not implemented).
- Runtime tracker options currently supported: `TRACKER_TYPE=none|iou|bytetrack`.

Status
------
- IOU tracker: implemented
- ByteTrack: optional (fallback to IOU when deps missing)
- DeepSORT: not implemented (future)

Related Docs
------------
- Contract: `docs/packs/vision/event_protocol_v0.2.md`
- Model I/O: `docs/packs/vision/model_interface.md`
- Pipeline behavior: `legacy/docs/legacy/specs/legacy_pipeline_spec.md`

## 한국어
목적
-----
모델 어댑터 파이프라인에 트래킹(안정적인 `track_id`)을 어떻게 붙일지 정의한다.

범위
----
- PERSON의 track_id는 `docs/packs/vision/event_protocol_v0.2.md` 기준 필수.
- FIRE/SMOKE는 track_id가 없어도 된다.
- IOU 트래커는 구현 완료, ByteTrack은 의존성 있을 때만 선택.
- DeepSORT는 향후 확장 항목(현재 미구현).
- 현재 런타임 트래커 옵션: `TRACKER_TYPE=none|iou|bytetrack`.

상태
----
- IOU 트래커: 구현 완료
- ByteTrack: 선택(의존성 없으면 IOU 폴백)
- DeepSORT: 미구현(향후 확장)

관련 문서
---------
- 계약: `docs/packs/vision/event_protocol_v0.2.md`
- 모델 입출력: `docs/packs/vision/model_interface.md`
- 파이프라인 동작: `legacy/docs/legacy/specs/legacy_pipeline_spec.md`
