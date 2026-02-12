# Event Protocol v0.2 (Person + Fire/Smoke + PPE/Posture/Hazard)

## English

## Common Rules

### Coordinate System

- All coordinates are pixel coordinates in the video frame
- Origin `(0,0)` is **top-left**
- `x` increases to the right, `y` increases downward
- Example: `(120,80)` means 120px from left, 80px from top

### Zone Inside Rule (common)

- `inside=true` is decided by computing a **rule_point** per `event_type`, then checking if it is inside the zone polygon
- rule_point:
  - **Person intrusion (`ZONE_INTRUSION`, `object_type=PERSON`)**
    `bottom_center = ((x1+x2)/2, y2)`
  - **Fire/Smoke (`FIRE_DETECTED`, `SMOKE_DETECTED`, `object_type=FIRE|SMOKE`)**
    `bbox_center = ((x1+x2)/2, (y1+y2)/2)` *(recommended)*

> Note: You may unify all types to bottom_center, but bbox_center is more natural for fire/smoke.

---

## 1) Event JSON Schema (AI -> Backend)

### Field summary

- **Required**: `event_id`, `ts`, `site_id`, `camera_id`, `event_type`, `severity`, `bbox`, `confidence`, `zone`
- **Conditional**:
  - `track_id`: **required** for `object_type=PERSON`, **optional** for FIRE/SMOKE
  - `object_type`: **recommended (effectively required)** to simplify frontend/IoT
  - `snapshot_path`: **required when snapshot is enabled and saved successfully**; otherwise null/omitted
  - `sensor`: optional object (nearest matched sensor packet) or null
- **Runtime extension event types**:
  - `SENSOR_EVENT`: independent sensor packet event
  - `FUSED_EVENT`: vision event + nearest sensor packet fused output

### Example 1) Person Zone Intrusion

```jsonc
{
  "event_id": "2f7f3e6a-3c0e-4f3b-9a2e-5f1d7d0b9f3a",
  // Unique event ID (typically UUID)

  "ts": "2026-01-28T14:03:21+09:00",
  // Event time (ISO-8601). +09:00 is KST.
  // Recommended: frame capture time

  "site_id": "S001",
  // Site ID

  "camera_id": "cam01",
  // Camera ID

  "event_type": "ZONE_INTRUSION",
  // Event category

  "object_type": "PERSON",
  // Type of object detected

  "severity": "CRITICAL",
  // Severity level: INFO, LOW, MEDIUM, HIGH, CRITICAL

  "track_id": 102,
  // Object tracking ID (integer)

  "bbox": {
    "x1": 450,
    "y1": 200,
    "x2": 520,
    "y2": 410
  },
  // Bounding box in pixel coordinates

  "confidence": 0.88,
  // AI model confidence score (0.0 to 1.0)

  "zone": {
    "zone_id": "Z-01",
    "inside": true
  },
  // Evaluation of rule_point vs zone polygon

  "snapshot_path": "/snapshots/20260128/S001_cam01_20260128140321_102.jpg",
  // Publicly accessible URL or relative path to the frame image

  "sensor": {
    "sensor_id": "ultrasonic-front-01",
    "sensor_type": "ultrasonic",
    "sensor_ts": "2026-01-28T14:03:21+09:00",
    "distance_cm": 82.4
  }
  // Optional nearest sensor packet attached by sensor lane
}
```

---

## 2) Heartbeat JSON Schema (AI -> Backend)

- **Purpose**: Sent periodically to inform the backend that the AI pipeline is alive.

```jsonc
{
  "ts": "2026-01-28T14:04:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "HEARTBEAT",
  "last_frame_age_sec": 0.05
  // Time elapsed since the last processed frame
}
```

---

## 3) Metrics JSON Schema (AI -> Backend/Observability)

- **Purpose**: Cumulative statistics since pipeline start (or interval reset).
- **Metric semantics**:
  - `events` / `events_accepted`: accepted at emitter boundary (`emit()==True`)
  - `backend_ack_ok` / `backend_ack_fail`: actual backend delivery result (ACK)
  - `errors`: ingest/read path errors (not backend POST errors)
  - `sensor_packets_total` / `sensor_packets_dropped` / `sensor_source_errors`: sensor lane health
  - `fusion_attempts` / `fusion_hits` / `fusion_misses`: fusion matching quality

```jsonc
{
  "ts": "2026-01-28T14:05:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "METRICS",
  "metrics": {
    "uptime_sec": 3600.5,
    "fps": 9.98,
    "frames": 36000,
    "drops": 120,
    "events": 12,
    "events_accepted": 12,
    "backend_ack_ok": 11,
    "backend_ack_fail": 1,
    "errors": 0,
    "sensor_packets_total": 100,
    "sensor_packets_dropped": 2,
    "sensor_source_errors": 0,
    "fusion_attempts": 10,
    "fusion_hits": 9,
    "fusion_misses": 1
  }
}
```

---

## 한국어

이벤트 프로토콜 v0.2 (사람 + 화재/연기 + PPE/자세/위험지역)
======================================================

## 공통 규칙

### 좌표 기준

- 모든 좌표는 영상 프레임 내의 픽셀 좌표임
- 원점 `(0,0)`은 **좌측 상단(top-left)**임
- `x`는 우측으로 증가, `y`는 하단으로 증가함
- 예: `(120,80)`은 왼쪽에서 120px, 위쪽에서 80px 지점을 의미함

### 구역 진입 판정 (Zone Inside Rule)

- `inside=true` 여부는 `event_type`별로 정의된 **rule_point**를 계산한 뒤, 해당 점이 구역 폴리곤 내부에 있는지 확인하여 결정함
- rule_point 설정:
  - **사람 침입 (`ZONE_INTRUSION`, `object_type=PERSON`)**
    `bottom_center = ((x1+x2)/2, y2)` (바닥 접점)
  - **화재/연기 (`FIRE_DETECTED`, `SMOKE_DETECTED`, `object_type=FIRE|SMOKE`)**
    `bbox_center = ((x1+x2)/2, (y1+y2)/2)` (바운딩 박스 중심) *(권장)*

> 참고: 운영 정책에 따라 모든 타입을 bottom_center로 통일할 수 있으나, 화재/연기는 bbox_center가 더 자연스러움.

---

## 1) 이벤트 JSON 스키마 (AI -> 백엔드)

### 필드 요약

- **필수**: `event_id`, `ts`, `site_id`, `camera_id`, `event_type`, `severity`, `bbox`, `confidence`, `zone`
- **조건부 필수**:
  - `track_id`: `object_type=PERSON`인 경우 **필수**, 화재/연기는 선택 사항
  - `object_type`: 프론트엔드/IoT 연동 편의를 위해 **권장 (사실상 필수)**
  - `snapshot_path`: 스냅샷 기능이 활성화되고 성공적으로 저장된 경우 **필수**, 그 외에는 null 또는 생략
  - `sensor`: 선택 객체(가장 가까운 센서 패킷) 또는 null
- **런타임 확장 이벤트 타입**:
  - `SENSOR_EVENT`: 센서 패킷 독립 이벤트
  - `FUSED_EVENT`: 비전 이벤트 + 최근 센서 패킷 융합 출력

### 예시 1) 사람 구역 침입

```jsonc
{
  "event_id": "2f7f3e6a-3c0e-4f3b-9a2e-5f1d7d0b9f3a",
  // 이벤트 고유 ID (보통 UUID)

  "ts": "2026-01-28T14:03:21+09:00",
  // 이벤트 발생 시간 (ISO-8601). +09:00은 한국 표준시(KST).
  // 권장: 프레임 캡처 시간

  "site_id": "S001",
  // 사이트(현장) ID

  "camera_id": "cam01",
  // 카메라 ID

  "event_type": "ZONE_INTRUSION",
  // 이벤트 카테고리 (구역 침입)

  "object_type": "PERSON",
  // 탐지된 객체 타입

  "severity": "CRITICAL",
  // 위험도 레벨: INFO, LOW, MEDIUM, HIGH, CRITICAL

  "track_id": 102,
  // 객체 추적 ID (정수형)

  "bbox": {
    "x1": 450,
    "y1": 200,
    "x2": 520,
    "y2": 410
  },
  // 픽셀 좌표 기준 바운딩 박스

  "confidence": 0.88,
  // AI 모델 신뢰도 (0.0 ~ 1.0)

  "zone": {
    "zone_id": "Z-01",
    "inside": true
  },
  // rule_point와 구역 폴리곤 비교 결과

  "snapshot_path": "/snapshots/20260128/S001_cam01_20260128140321_102.jpg",
  // 공개 가능한 스냅샷 이미지 경로 또는 상대 경로

  "sensor": {
    "sensor_id": "ultrasonic-front-01",
    "sensor_type": "ultrasonic",
    "sensor_ts": "2026-01-28T14:03:21+09:00",
    "distance_cm": 82.4
  }
  // 센서 축에서 주입된 최근 센서 패킷(선택)
}
```

---

## 2) 하트비트 JSON 스키마 (AI -> 백엔드)

- **목적**: AI 파이프라인이 정상 작동 중임을 백엔드에 주기적으로 알림.

```jsonc
{
  "ts": "2026-01-28T14:04:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "HEARTBEAT",
  "last_frame_age_sec": 0.05
  // 마지막으로 처리된 프레임으로부터 경과된 시간(초)
}
```

---

## 3) 메트릭 JSON 스키마 (AI -> 백엔드/관측 시스템)

- **목적**: 파이프라인 시작 이후(또는 초기화 이후) 누적된 통계 정보 제공.
- **메트릭 의미**:
  - `events` / `events_accepted`: 에미터 경계에서 수락된 건수 (`emit()==True`)
  - `backend_ack_ok` / `backend_ack_fail`: 실제 백엔드 전달 결과(ACK)
  - `errors`: ingest/read 경로 오류 집계 (backend POST 오류는 제외)
  - `sensor_packets_total` / `sensor_packets_dropped` / `sensor_source_errors`: 센서 축 상태
  - `fusion_attempts` / `fusion_hits` / `fusion_misses`: 융합 매칭 품질

```jsonc
{
  "ts": "2026-01-28T14:05:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "METRICS",
  "metrics": {
    "uptime_sec": 3600.5,
    "fps": 9.98,
    "frames": 36000,
    "drops": 120,
    "events": 12,
    "events_accepted": 12,
    "backend_ack_ok": 11,
    "backend_ack_fail": 1,
    "errors": 0,
    "sensor_packets_total": 100,
    "sensor_packets_dropped": 2,
    "sensor_source_errors": 0,
    "fusion_attempts": 10,
    "fusion_hits": 9,
    "fusion_misses": 1
  }
}
```
