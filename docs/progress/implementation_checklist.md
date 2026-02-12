# Implementation Checklist

## English

Purpose
-------

Track overall pipeline readiness (non-model + model). As of 2026-02-10, non-model code is implemented and audited (G1-G10, 154 tests); real RTSP device validation and production model accuracy are still pending.

Status Legend
-------------

- [ ] not started
- [~] in progress
- [x] done

Root
----

- [x] RTSP Stability
  - [x] Reconnect strategy (retry/backoff, max attempts)
  - [x] Timeout handling (read timeout, watchdog)
  - [x] Sampling control (fps limit)
  - [x] Health reporting (last frame time, fps, error count)

- [x] Zones & Rules
  - [x] Zone source selector (api | file)
  - [x] Zone loader (GET /api/sites/{site}/cameras/{camera}/zones)
  - [x] Polygon geometry (point-in-polygon)
  - [x] Rule point policy (bottom_center vs bbox_center per event_type)
  - [x] Zone inside evaluation per frame

- [x] Event Dedup / Cooldown
  - [x] Key strategy (camera_id, track_id, event_type)
  - [x] Cooldown timers (per key)
  - [x] Severity change override (immediate re-emit)

- [x] Snapshot Handling
  - [x] Snapshot storage path layout
  - [x] Snapshot save on event
  - [x] snapshot_path/public mapping

- [x] Backend Integration
  - [x] Final event schema alignment (protocol.md)
  - [x] Error handling policy (retry/skip/drop)
  - [ ] Response handling (ack/trace_id) (backend pending)

- [x] Observability
  - [x] Metrics: fps, drops, events/sec
  - [x] Structured logging option
  - [x] Heartbeat log

- [x] Configuration & Env
  - [x] Config schema validation
  - [x] Environment overrides (env vars)
  - [x] Runtime mode (dev/prod)

- [x] Testing
  - [x] Unit tests for sampler/dedup
  - [x] Integration test with sample mp4
  - [x] Mock backend regression (jsonl comparison)

- [x] Packaging & Run
  - [x] Dockerfile
  - [x] Entrypoint script
  - [ ] Systemd/cron example (not provided)

- [ ] Model Integration
  - [x] Adapter interface/loader
  - [x] Baseline adapters (YOLO/ONNX)
  - [x] Multi-detection support
  - [x] Visualization (`--visualize`)
  - [x] Multi-model merge (multiple adapters)
  - [x] Class mapping support (`MODEL_CLASS_MAP_PATH`)
  - [x] Tracker integration (real track_id via IOU)
  - [~] Real model accuracy validation (template ready)
  - [ ] Model deployment/runtime profiling (GPU/Jetson)
  - [x] Data collection plan (doc)
  - [x] Labeling guide (doc)
  - [x] Train/val/test split policy (doc)
  - [x] Training report template (doc)

Notes
-----

- Remaining gaps: real RTSP environment validation and model accuracy validation.

Code Mapping
------------

- RTSP: `src/ai/pipeline/sources/rtsp.py`, `src/ai/pipeline/core.py`
- Zones: `src/ai/rules/zones.py`
- Dedup: `src/ai/rules/dedup.py`
- Snapshots: `src/ai/events/snapshot.py`, `src/ai/pipeline/events.py`
- Backend: `src/ai/clients/backend_api.py`, `src/ai/pipeline/emitter.py`
- Observability: `src/ai/logging_setup.py`, `src/ai/utils/metrics.py`
- Config: `src/ai/pipeline/config.py`, `src/ai/config.py`
- Tests: `tests/`

## 한국어

목적
-----

전체 파이프라인(비모델 + 모델)의 준비 상태를 체크리스트로 관리한다. 2026-02-10 기준으로 비모델 구현 및 감사(G1-G10, 테스트 154개)가 완료되었고, 실장비 RTSP 검증과 모델 정확도 검증은 미완이다.

상태 표기
---------

- [ ] 미시작
- [~] 진행 중
- [x] 완료

루트
----

- [x] RTSP 안정화
  - [x] 재연결 전략 (재시도/백오프, 최대 시도)
  - [x] 타임아웃 처리 (read 타임아웃, watchdog)
  - [x] 샘플링 제어 (fps 제한)
  - [x] 상태 보고 (마지막 프레임 시간, fps, 에러 카운트)

- [x] Zones & Rules
  - [x] Zone 소스 선택 (api | file)
  - [x] Zone 로더 (GET /api/sites/{site}/cameras/{camera}/zones)
  - [x] 폴리곤 기하 (point-in-polygon)
  - [x] 룰 포인트 정책 (event_type별 bottom_center vs bbox_center)
  - [x] 프레임별 zone inside 평가

- [x] 이벤트 중복 억제 / 쿨다운
  - [x] 키 전략 (camera_id, track_id, event_type)
  - [x] 쿨다운 타이머 (키별)
  - [x] severity 변경 시 즉시 재발행

- [x] 스냅샷 처리
  - [x] 스냅샷 저장 경로 레이아웃
  - [x] 이벤트 발생 시 스냅샷 저장
  - [x] snapshot_path/public 매핑

- [x] 백엔드 연동
  - [x] 이벤트 스키마 최종 정렬 (protocol.md)
  - [x] 에러 처리 정책 (재시도/스킵/드롭)
  - [ ] 응답 처리 (ack/trace_id) (백엔드 대기)

- [x] 관측성
  - [x] 메트릭: fps, drops, events/sec
  - [x] 구조화 로그 옵션
  - [x] 하트비트 로그

- [x] 설정 & 환경변수
  - [x] 설정 스키마 검증
  - [x] 환경변수 오버라이드 (환경 변수)
  - [x] 런타임 모드 (dev/prod)

- [x] 테스트
  - [x] sampler/dedup 단위 테스트
  - [x] 샘플 mp4 통합 테스트
  - [x] mock backend 회귀 테스트 (jsonl 비교)

- [x] 패키징 & 실행
  - [x] Dockerfile
  - [x] Entrypoint 스크립트
  - [ ] Systemd/cron 예시 (미제공)

- [ ] 모델 연동
  - [x] 어댑터 인터페이스/로더
  - [x] 기준 어댑터(YOLO/ONNX)
  - [x] 다중 detection 지원
  - [x] 시각화(`--visualize`)
  - [x] 다중 모델 병합(여러 어댑터)
  - [x] 클래스 매핑 지원(`MODEL_CLASS_MAP_PATH`)
  - [x] 트래커 연동(실 track_id, IOU 기준)
  - [~] 실제 모델 정확도 검증(템플릿 준비)
  - [ ] 모델 배포/런타임 프로파일링(GPU/Jetson)
  - [x] 데이터 수집 계획 (문서)
  - [x] 라벨링 가이드 (문서)
  - [x] 학습/검증/테스트 분리 정책 (문서)
  - [x] 학습 리포트 템플릿 (문서)

노트
----

- 남은 핵심: 실제 RTSP 환경 검증, 모델 정확도 검증.

코드 매핑
---------

- RTSP: `src/ai/pipeline/sources/rtsp.py`, `src/ai/pipeline/core.py`
- Zones: `src/ai/rules/zones.py`
- Dedup: `src/ai/rules/dedup.py`
- 스냅샷: `src/ai/events/snapshot.py`, `src/ai/pipeline/events.py`
- 백엔드: `src/ai/clients/backend_api.py`, `src/ai/pipeline/emitter.py`
- 관측성: `src/ai/logging_setup.py`, `src/ai/utils/metrics.py`
- 설정: `src/ai/pipeline/config.py`, `src/ai/config.py`
- 테스트: `tests/`
