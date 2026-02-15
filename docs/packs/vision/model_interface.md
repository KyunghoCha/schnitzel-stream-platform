# Vision Model Interface v2

Last updated: 2026-02-16

## English

## Purpose

Define the payload interface between a vision detection producer node and downstream event/policy nodes in v2 graphs.

## Detection Payload Contract

A detection packet payload is a dictionary with:

- `bbox`: `{"x1": int, "y1": int, "x2": int, "y2": int}`
- `confidence`: `float` (0.0 ~ 1.0)
- `event_type`: `str`
- `object_type`: `str`
- `severity`: `str`
- `track_id`: `int` (required when `object_type == "PERSON"`)

Optional fields:
- `snapshot_path`: `str | null`
- `sensor`: `dict | null`

## Producer/Consumer Mapping

- Example producer node: `src/schnitzel_stream/packs/vision/nodes/mock_detection.py`
- Event builder consumer: `src/schnitzel_stream/packs/vision/nodes/event_builder.py`
- Policy consumers: `src/schnitzel_stream/packs/vision/nodes/policy.py`

## Plugin Extension Pattern

Custom model node should:
1. receive `kind=frame` packet
2. emit `kind=detection` packet(s) with the contract above
3. keep non-portable objects (raw frames) inside in-proc boundary

---

## 한국어

## 목적

v2 그래프에서 비전 탐지 생성 노드와 하위 이벤트/정책 노드 사이의 payload 인터페이스를 정의한다.

## Detection Payload 계약

detection 패킷 payload는 아래 키를 갖는 dict다:

- `bbox`: `{"x1": int, "y1": int, "x2": int, "y2": int}`
- `confidence`: `float` (0.0 ~ 1.0)
- `event_type`: `str`
- `object_type`: `str`
- `severity`: `str`
- `track_id`: `int` (`object_type == "PERSON"`일 때 필수)

선택 필드:
- `snapshot_path`: `str | null`
- `sensor`: `dict | null`

## 생산자/소비자 매핑

- 예시 생산자 노드: `src/schnitzel_stream/packs/vision/nodes/mock_detection.py`
- 이벤트 빌더 소비자: `src/schnitzel_stream/packs/vision/nodes/event_builder.py`
- 정책 소비자: `src/schnitzel_stream/packs/vision/nodes/policy.py`

## 플러그인 확장 패턴

커스텀 모델 노드는 다음을 따라야 한다:
1. `kind=frame` 패킷 수신
2. 위 계약을 만족하는 `kind=detection` 패킷 출력
3. raw frame 같은 비이식 객체는 in-proc 경계 내에서만 처리
