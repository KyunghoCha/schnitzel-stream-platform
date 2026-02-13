# multimodal_pipeline_design

## English

Multimodal Pipeline Design (Video + Sensor)
===========================================

## Objective

Define a production-safe extension path from video-only pipeline to multimodal runtime (video + IoT/ROS2 sensors), without breaking existing camera operations.

Implementation status (2026-02-10): P2 baseline is implemented (`SensorRuntime` collector, nearest time-window attachment, optional `SENSOR_EVENT`/`FUSED_EVENT` outputs, and sensor/fusion metrics fields). Production hardening remains next.

## Why This Design

- Current runtime is strongly optimized for video frames (`FrameSource`).
- Sensor signals (ultrasonic, PLC, gas, etc.) are structurally different from frames.
- Over-generalizing too early into a single universal input interface adds complexity and regression risk.
- Therefore this design uses **two input lanes** with a narrow fusion boundary.

## Scope / Non-Scope

- In scope:
  - Runtime architecture for video + sensor ingestion
  - Interface contracts for extensibility
  - Time synchronization and event correlation model
  - Process topology options and recommended deployment
  - Security, observability, and test strategy without real hardware
- Out of scope (for this phase):
  - Vendor-specific sensor drivers
  - Final backend schema migration
  - Full hardware validation results

## Design Principles

1. Keep current camera pipeline stable by default.
2. Add sensor path incrementally, not by rewriting core pipeline.
3. Explicit contracts over implicit coupling.
4. Fail-fast on invalid plugin/config.
5. Keep mock strictly test-only; production defaults remain real-mode.

## Target Architecture

### Input Lanes

- **Video lane**: `VideoSource` (existing `FrameSource` lineage)
  - file / rtsp / webcam / plugin
- **Sensor lane**: `SensorSource` (new)
  - ros2 / mqtt / modbus / serial / plugin

### Fusion Boundary

- Sensor data and frame-derived events meet only at one stage:
  - `FusionEngine` (or `FusionRuleEvaluator`) between event build and final emit

### Output Lanes

- Existing emitter model remains:
  - backend / stdout / file / plugin

## Process Topology

### Option A: Single process (PoC)

- One process reads video + sensor and emits events.
- Pros: fastest to start.
- Cons: weaker isolation, harder fault containment.

### Option B: Split ingestion (recommended for production)

- Camera pipeline process per camera (or per camera group)
- Sensor collector process (shared)
- Fusion at runtime via local IPC/cache/topic
- Pros: strong fault isolation, better scale profile.

### Option C: Fully isolated per source

- One process per camera and per sensor adapter.
- Use only for high-risk/high-throughput sites.

## Data Contracts

### VideoFrame (runtime internal)

- `camera_id: str`
- `frame_ts: datetime` (capture timestamp)
- `ingest_ts: datetime` (runtime receive timestamp)
- `frame: ndarray`

### SensorPacket (new runtime internal contract)

- `sensor_id: str`
- `sensor_type: str` (ultrasonic, gas, plc, ...)
- `source_ts: datetime | None` (device timestamp if available)
- `ingest_ts: datetime` (runtime receive timestamp)
- `value: float | int | bool | str | dict`
- `unit: str | None`
- `quality: str | None` (ok, stale, invalid, ...)
- `meta: dict[str, Any]`

### Event Types (proposed)

- `vision_event`: frame-origin event
- `sensor_event`: sensor-origin event (no mandatory bbox)
- `fused_event`: correlated result from video + sensor

Note: backend-facing schema extension should be versioned in `docs/contracts/protocol.md` when implementation begins.

## Time Synchronization Model

### Timestamp Fields

- Keep both timestamps whenever possible:
  - `source_ts`: timestamp from external device/source
  - `ingest_ts`: timestamp when runtime received data
- For vision pipeline, keep `frame_ts` as event reference time.

### Correlation Rule

- Fusion engine correlates by time window:
  - default candidate window: `frame_ts ± 200~500ms` (site-tuned)
- Select nearest sensor packet in window by absolute time delta.
- If none exists:
  - emit vision-only event with sensor state `missing` or
  - suppress fused event by policy.

### Clock Discipline

- Require NTP/chrony synchronization across edge devices.
- Track drift metric per source: `abs(source_ts - ingest_ts)`.

## Concurrency / Backpressure

- Use bounded queues for sensor ingest and fusion staging.
- On queue full:
  - drop oldest for high-rate sensors or
  - drop newest for critical low-rate sensors (policy per source)
- Expose drop counters in metrics.

## Security Model

1. Plugin path allowlist in production (`ALLOWED_PLUGIN_PREFIXES`).
2. No implicit plugin loading; explicit config/env only.
3. Sensor credentials must be injected by secret/env, not hardcoded in yaml.
4. Validate payload type/range at adapter boundary.

## Observability Additions

Add sensor/fusion metrics (names tentative):

- `sensor_packets_total`
- `sensor_packets_dropped`
- `sensor_source_errors`
- `fusion_attempts`
- `fusion_hits`
- `fusion_misses`
- `sensor_clock_skew_ms`

## No-Hardware Test Strategy

1. ROS2 topic replay (recorded or synthetic publisher)
2. MQTT/serial fake publisher scripts
3. Deterministic fixture-based fusion tests
4. Fault injection:
  - delayed sensor packet
  - out-of-order timestamp
  - malformed payload
  - sensor disconnect/reconnect

## Phased Rollout Plan

### P0: Architecture & contract freeze (doc + skeleton)

- Add `SensorSource` protocol and loader (no runtime wiring yet)
- Add config schema placeholders (`sensor.*`)
- Add unit tests for loader/validation

### P1: Sensor ingest attachment (implemented)

- Add runtime sensor collector (`SensorRuntime`) with bounded buffer
- Attach nearest sensor packet to each vision event (`payload.sensor`) by time window
- Provide no-hardware reference adapter (`FakeUltrasonicSensorSource`)

### P2: Sensor event + fusion (baseline implemented)

- Emit `SENSOR_EVENT` independently (optional policy)
- Add sensor/fusion metrics fields
- Add nearest time-window fusion wrapper (`FUSED_EVENT`)
- Add deterministic no-hardware sensor lane tests

### P3: Production hardening

- Plugin allowlist enforcement in prod profile
- Backpressure policy tuning
- Soak tests and operational runbook completion

## Acceptance Criteria

1. Existing video-only runs unchanged by default.
2. Sensor plugin failure does not crash unrelated camera processes (split topology).
3. Fusion behavior is deterministic under replay tests.
4. Event/schema changes are versioned and documented.

## Code Mapping

- Sensor contracts/loader/runtime: `src/ai/pipeline/sensors/protocol.py`, `src/ai/pipeline/sensors/loader.py`, `src/ai/pipeline/sensors/runtime.py`
- Sensor/fusion builders: `src/ai/pipeline/sensors/builder.py`, `src/ai/pipeline/sensors/fusion.py`
- Reference sensor plugin: `src/ai/plugins/sensors/fake_ultrasonic.py`
- Phase 0 runtime wiring: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`, `src/ai/pipeline/core.py`
- Docs SSOT updates: `docs/specs/pipeline_spec.md`, `docs/contracts/protocol.md`

---

## 한국어

멀티모달 파이프라인 설계 (영상 + 센서)
======================================

## 목적

현재 영상 중심 파이프라인을 깨뜨리지 않고, IoT/ROS2 센서를 운영 가능한 방식으로 확장하기 위한 기준 아키텍처를 정의한다.

구현 상태(2026-02-10): P2 기반(`SensorRuntime` 수집기, 시간창 최근 매칭 주입, 선택적 `SENSOR_EVENT`/`FUSED_EVENT` 출력, 센서/융합 메트릭 필드)까지 반영됨. 다음 단계는 운영 하드닝이다.

## 이 설계를 택한 이유

- 현재 런타임은 `FrameSource` 기반 영상 처리에 최적화되어 있음.
- 센서 신호(초음파, PLC, 가스 등)는 프레임과 데이터 형태가 다름.
- 성급한 단일 만능 입력 인터페이스는 복잡도/회귀 리스크를 키움.
- 따라서 **입력 2축(영상/센서) + 단일 융합 경계** 전략을 채택한다.

## 범위 / 비범위

- 범위:
  - 영상+센서 수집 런타임 구조
  - 확장 인터페이스 계약
  - 시간 동기화/상관관계 모델
  - 프로세스 토폴로지 및 권장 운영 방식
  - 무실장비 테스트, 보안/관측성 기준
- 비범위(이번 단계):
  - 벤더별 드라이버 상세
  - 백엔드 최종 스키마 마이그레이션
  - 실장비 최종 성능 수치

## 설계 원칙

1. 기본 카메라 경로 안정성을 우선 보장한다.
2. 센서 경로는 코어 재작성 없이 단계적으로 추가한다.
3. 암묵 결합 대신 명시 계약을 사용한다.
4. 플러그인/설정 오류는 즉시 실패(fail-fast)한다.
5. mock는 테스트 전용으로 유지하고 실사용 기본값은 real로 유지한다.

## 목표 아키텍처

### 입력 축

- **영상 축**: `VideoSource` (기존 `FrameSource` 계열)
  - file / rtsp / webcam / plugin
- **센서 축**: `SensorSource` (신규)
  - ros2 / mqtt / modbus / serial / plugin

### 융합 경계

- 영상 이벤트와 센서 데이터는 한 지점에서만 결합:
  - `FusionEngine` (또는 `FusionRuleEvaluator`)

### 출력 축

- 기존 emitter 모델 유지:
  - backend / stdout / file / plugin

## 프로세스 토폴로지

### 옵션 A: 단일 프로세스(PoC)

- 한 프로세스에서 영상+센서를 모두 수집/전송.
- 장점: 빠른 PoC.
- 단점: 장애 격리 약함.

### 옵션 B: 수집 분리(운영 권장)

- 카메라 파이프라인 프로세스(카메라별 또는 그룹별)
- 센서 수집 프로세스(공용)
- 로컬 IPC/캐시/토픽으로 융합
- 장점: 장애 격리/확장성 우수.

### 옵션 C: 완전 분리

- 카메라별 + 센서별 개별 프로세스.
- 초고부하/고위험 환경에서만 적용.

## 데이터 계약

### VideoFrame (런타임 내부)

- `camera_id: str`
- `frame_ts: datetime` (캡처 시각)
- `ingest_ts: datetime` (수신 시각)
- `frame: ndarray`

### SensorPacket (신규 런타임 내부 계약)

- `sensor_id: str`
- `sensor_type: str` (ultrasonic, gas, plc, ...)
- `source_ts: datetime | None` (장비 시각)
- `ingest_ts: datetime` (런타임 수신 시각)
- `value: float | int | bool | str | dict`
- `unit: str | None`
- `quality: str | None` (`ok`, `stale`, `invalid` ...)
- `meta: dict[str, Any]`

### 이벤트 타입(제안)

- `vision_event`: 프레임 기반 이벤트
- `sensor_event`: 센서 기반 이벤트(필수 bbox 없음)
- `fused_event`: 영상+센서 융합 이벤트

주의: 구현 단계에서 백엔드 스키마 확장은 `docs/contracts/protocol.md` 버전 업으로 관리한다.

## 시간 동기화 모델

### 타임스탬프 정책

- 가능한 경우 두 시각을 모두 저장:
  - `source_ts`: 외부 장비/원천 시각
  - `ingest_ts`: 런타임 수신 시각
- 영상 이벤트 기준 시각은 `frame_ts`를 사용.

### 상관관계 규칙

- `FusionEngine`은 시간 윈도우 기반으로 결합:
  - 기본 윈도우: `frame_ts ± 200~500ms` (현장 튜닝)
- 윈도우 내에서 절대 시간 차이가 최소인 센서값 선택.
- 윈도우에 값이 없으면:
  - 비전 단독 이벤트로 유지(sensor 상태 `missing`) 또는
  - 정책에 따라 융합 이벤트 미생성.

### 시계 동기

- 엣지 장비 전반 NTP/chrony 동기화 필수.
- 소스별 드리프트 `abs(source_ts - ingest_ts)`를 메트릭으로 관리.

## 동시성 / 백프레셔

- 센서 수집/융합 단계는 bounded queue 사용.
- queue full 시:
  - 고주기 센서는 oldest drop 우선 또는
  - 저주기/중요 센서는 newest drop 정책 선택
- drop 카운터는 메트릭으로 노출.

## 보안 모델

1. 프로덕션에서 플러그인 allowlist 강제 (`ALLOWED_PLUGIN_PREFIXES`).
2. 플러그인은 명시 설정/env로만 로드.
3. 센서 인증정보는 yaml 하드코딩 금지(시크릿/env 주입).
4. 어댑터 경계에서 타입/범위 검증 필수.

## 관측성 확장

추가 메트릭(안):

- `sensor_packets_total`
- `sensor_packets_dropped`
- `sensor_source_errors`
- `fusion_attempts`
- `fusion_hits`
- `fusion_misses`
- `sensor_clock_skew_ms`

## 무실장비 테스트 전략

1. ROS2 토픽 replay(기록 파일 또는 synthetic publisher)
2. MQTT/serial fake publisher
3. fixture 기반 결정적 fusion 테스트
4. 장애 주입:
  - 센서 지연
  - out-of-order timestamp
  - malformed payload
  - disconnect/reconnect

## 단계별 적용 계획

### P0: 아키텍처/계약 고정(문서+골격)

- `SensorSource` 프로토콜/로더 추가(런타임 연결은 보류)
- `sensor.*` 설정 스키마 자리 추가
- 로더/검증 단위 테스트 추가

### P1: 센서 수집 주입(구현됨)

- `SensorRuntime` 기반 센서 수집 + bounded buffer 추가
- 시간 윈도우 기준으로 각 비전 이벤트의 `sensor` 필드에 최근 패킷 주입
- 무실장비 기준 어댑터(`FakeUltrasonicSensorSource`) 추가

### P2: 센서 이벤트 + 융합 (기반 구현됨)

- `SENSOR_EVENT` 단독 전송 경로(정책 옵션) 추가
- 센서/융합 메트릭 필드 추가
- 시간창 최근 매칭 기반 `FUSED_EVENT` 출력 추가
- 무실장비 기반 결정적 센서 lane 테스트 추가

### P3: 운영 보강

- prod 프로필에서 플러그인 allowlist 강제
- 백프레셔 정책 튜닝
- soak 테스트 + 운영 런북 완성

## 완료 기준

1. 기본 영상-only 실행이 변경 없이 유지된다.
2. 센서 플러그인 장애가 무관한 카메라 프로세스를 죽이지 않는다(분리 토폴로지 기준).
3. replay 테스트에서 fusion 결과가 결정적이다.
4. 이벤트/스키마 변경은 버전과 문서로 추적된다.

## 코드 매핑

- Sensor 계약/로더/런타임: `src/ai/pipeline/sensors/protocol.py`, `src/ai/pipeline/sensors/loader.py`, `src/ai/pipeline/sensors/runtime.py`
- Sensor/Fusion 빌더: `src/ai/pipeline/sensors/builder.py`, `src/ai/pipeline/sensors/fusion.py`
- 기준 센서 플러그인: `src/ai/plugins/sensors/fake_ultrasonic.py`
- Phase 0 런타임 연결 지점: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`, `src/ai/pipeline/core.py`
- SSOT 반영 대상: `docs/specs/pipeline_spec.md`, `docs/contracts/protocol.md`
