# Model I/O Samples v0.2

## English

## Purpose

Provides concrete JSON examples for different detection scenarios. These samples should be used for testing adapters and validating backend integration.

## 1. Person Zone Intrusion

Detected a person inside a restricted zone.

```jsonc
{
  "event_id": "8a1b2c3d-...",
  "ts": "2026-02-01T10:00:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "ZONE_INTRUSION",
  "object_type": "PERSON",
  "severity": "HIGH",
  "track_id": 42,
  "bbox": {"x1": 100, "y1": 200, "x2": 150, "y2": 350},
  "confidence": 0.95,
  "zone": {"zone_id": "dangerous-area", "inside": true}
}
```

## 2. Fire Detection

Fire detected in the frame. Usually does not require `track_id` but requires `object_type=FIRE`.

```jsonc
{
  "event_id": "9b2c3d4e-...",
  "ts": "2026-02-01T10:05:00+09:00",
  "site_id": "S001",
  "camera_id": "cam02",
  "event_type": "FIRE_DETECTED",
  "object_type": "FIRE",
  "severity": "CRITICAL",
  "bbox": {"x1": 500, "y1": 400, "x2": 600, "y2": 500},
  "confidence": 0.82,
  "zone": {"zone_id": "factory-floor", "inside": true}
}
```

## 3. PPE Violation

A person is detected without a helmet in a mandatory PPE zone.

```jsonc
{
  "event_id": "af1f2e3d-...",
  "ts": "2026-02-01T10:10:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "PPE_VIOLATION",
  "object_type": "NO_HELMET",
  "severity": "MEDIUM",
  "track_id": 43,
  "bbox": {"x1": 200, "y1": 100, "x2": 250, "y2": 150},
  "confidence": 0.75,
  "zone": {"zone_id": "ppe-required-zone", "inside": true}
}
```

---

## 한국어

모델 I/O 샘플 v0.2
================

## 목적

다양한 탐지 시나리오에 대한 실제 JSON 예시를 제공함. 이 샘플들은 어댑터 테스트 및 백엔드 연동 검증용으로 사용됨.

## 1. 사람 구역 침입

제한 구역 내에서 사람이 감지된 경우.

```jsonc
{
  "event_id": "8a1b2c3d-...",
  "ts": "2026-02-01T10:00:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "ZONE_INTRUSION",
  "object_type": "PERSON",
  "severity": "HIGH",
  "track_id": 42,
  "bbox": {"x1": 100, "y1": 200, "x2": 150, "y2": 350},
  "confidence": 0.95,
  "zone": {"zone_id": "dangerous-area", "inside": true}
}
```

## 2. 화재 탐지

화면 내에서 화재가 감지된 경우. 일반적으로 `track_id`는 필수적이지 않으나 `object_type=FIRE`가 필요함.

```jsonc
{
  "event_id": "9b2c3d4e-...",
  "ts": "2026-02-01T10:05:00+09:00",
  "site_id": "S001",
  "camera_id": "cam02",
  "event_type": "FIRE_DETECTED",
  "object_type": "FIRE",
  "severity": "CRITICAL",
  "bbox": {"x1": 500, "y1": 400, "x2": 600, "y2": 500},
  "confidence": 0.82,
  "zone": {"zone_id": "factory-floor", "inside": true}
}
```

## 3. PPE 미착용 (안전모)

안전모 착용 필수 구역에서 안전모를 쓰지 않은 사람이 감지된 경우.

```jsonc
{
  "event_id": "af1f2e3d-...",
  "ts": "2026-02-01T10:10:00+09:00",
  "site_id": "S001",
  "camera_id": "cam01",
  "event_type": "PPE_VIOLATION",
  "object_type": "NO_HELMET",
  "severity": "MEDIUM",
  "track_id": 43,
  "bbox": {"x1": 200, "y1": 100, "x2": 250, "y2": 150},
  "confidence": 0.75,
  "zone": {"zone_id": "ppe-required-zone", "inside": true}
}
```
