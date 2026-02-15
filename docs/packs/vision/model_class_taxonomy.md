# Model Class Taxonomy v0.2

## English

## Purpose

Define the standardized list of `object_type` and `event_type` for all AI models in the safety system. This ensures that the backend and frontend treat detections consistently.

## 1. Core Objects & Detection Rules

| Object Type | Description | Primary Event Type | Severity |
| :--- | :--- | :--- | :--- |
| `PERSON` | General person detection | `ZONE_INTRUSION` | MEDIUM |
| `FIRE` | Visual fire/flames | `FIRE_DETECTED` | CRITICAL |
| `SMOKE` | Visual smoke plumes | `SMOKE_DETECTED` | HIGH |
| `FORKLIFT` | Heavy machinery (Forklift) | `ZONE_INTRUSION` | MEDIUM |

## 2. Safety & PPE (Personal Protective Equipment)

| Object Type | Description | Event Type | Severity |
| :--- | :--- | :--- | :--- |
| `HELMET` | Safety helmet worn | `PPE_COMPLIANCE` | INFO |
| `NO_HELMET` | Person without helmet | `PPE_VIOLATION` | MEDIUM |
| `VEST` | Safety vest worn | `PPE_COMPLIANCE` | INFO |
| `NO_VEST` | Person without vest | `PPE_VIOLATION` | LOW |

## 3. Posture & Activity

| Object Type | Description | Event Type | Severity |
| :--- | :--- | :--- | :--- |
| `FALLEN_PERSON` | Person lying on floor | `FALL_DETECTED` | HIGH |
| `POSTURE_HAZARD` | Dangerous posture (leaning) | `POSTURE_WARNING` | LOW |

---

## 한국어

모델 클래스 분류 체계 v0.2
========================

## 목적

안전 시스템의 모든 AI 모델에서 사용하는 `object_type` 및 `event_type`의 표준 리스트를 정의함. 이를 통해 백엔드와 프론트엔드가 탐지 결과를 일관되게 처리할 수 있도록 보장함.

## 1. 핵심 객체 및 탐지 규칙

| 객체 타입 (Object Type) | 설명 | 주요 이벤트 타입 | 위험도 (Severity) |
| :--- | :--- | :--- | :--- |
| `PERSON` | 일반 사람 탐지 | `ZONE_INTRUSION` | MEDIUM |
| `FIRE` | 육안상의 화염/불꽃 | `FIRE_DETECTED` | CRITICAL |
| `SMOKE` | 육안상의 연기 | `SMOKE_DETECTED` | HIGH |
| `FORKLIFT` | 지게차 등 중장비 | `ZONE_INTRUSION` | MEDIUM |

## 2. 안전 및 PPE (개인보호구)

| 객체 타입 (Object Type) | 설명 | 이벤트 타입 | 위험도 (Severity) |
| :--- | :--- | :--- | :--- |
| `HELMET` | 안전모 착용 중 | `PPE_COMPLIANCE` | INFO |
| `NO_HELMET` | 안전모 미착용 | `PPE_VIOLATION` | MEDIUM |
| `VEST` | 안전조끼 착용 중 | `PPE_COMPLIANCE` | INFO |
| `NO_VEST` | 안전조끼 미착용 | `PPE_VIOLATION` | LOW |

## 3. 자세 및 활동

| 객체 타입 (Object Type) | 설명 | 이벤트 타입 | 위험도 (Severity) |
| :--- | :--- | :--- | :--- |
| `FALLEN_PERSON` | 쓰러진 사람 감지 | `FALL_DETECTED` | HIGH |
| `POSTURE_HAZARD` | 위험한 자세 (기댐 등) | `POSTURE_WARNING` | LOW |
