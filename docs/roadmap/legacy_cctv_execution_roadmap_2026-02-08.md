# Industrial Safety CCTV Runtime Roadmap

## English

## Status (as of 2026-02-08)

### Final Goal

Deploy a multi-camera AI pipeline that ingests real RTSP streams, runs model/tracker inference, emits contract-compliant events to the backend, and supports stable operations with observability and runbooks.

### Target Outcomes

1) Real devices validated for RTSP stability, reconnect, and throughput.
2) Real backend integration validated end-to-end.
3) Model/tracker integrated with contract-compliant payloads.
4) Operations playbooks ready for handoff.
5) Model class taxonomy agreed and reflected in protocol.
6) Accuracy validation criteria and baseline metrics agreed.

### Model Scope (draft)

1) Required detections: person, intrusion, danger-zone entry.
2) Optional detections (phase 2+): PPE, posture, smoke, fire, hazard situations.
3) Any new class beyond the v0.2 list requires a protocol update.

### Assumptions / Open Decisions

1) Hardware target is not fixed (GPU, Jetson, or CPU-only).
2) Resolution/FPS/latency targets are TBD.
3) Budget target: ~KRW 1,000,000 (draft).
4) Final class taxonomy and severity rules require project policy lock (`docs/packs/vision/model_class_taxonomy.md`).
5) Labeling policy and training report format are defined in ops docs; owner confirmation is required.

### Completed

- Modular pipeline (Source/Sampler/Builder/Emitter/Core)
- File-based ingest + dummy event generation
- Model adapter interface + baseline adapters (YOLO/ONNX)
- Multi-model merge (comma-separated adapters)
- Zones & Rules integrated (zone load, rule_point, inside check)
- Event dedup (cooldown + severity override)
- Snapshot save (path creation/write/public mapping)
- Observability (metrics/heartbeat + json/plain logging)
- Config validation + env override + dev/prod profiles
- RTSP stability logic (reconnect/backoff/timeout, keep pipeline alive on read failure)
- Tests (unit + integration + regression + RTSP E2E host/docker) passing
- Docker packaging (Dockerfile, entrypoint)
- File ingest loop (`--loop`) + core FPS throttling (deterministic file-based testing)

### Remaining (completion criteria)

1) **Model/Tracker integration**. Baseline adapter done; IOU tracker done; accuracy validation remains.
2) **Real RTSP validation**. 실장비 스트림에서 reconnect/timeout 동작 확인.
3) **Real backend validation**. 실제 POST 성공/실패/타임아웃 정책 검증.
4) **Snapshot operational path**. 운영 환경 스냅샷 경로/권한 확인.
5) **Operations docs**. 운영 문서 보강(실운영 기준).
6) **Multi-Sensor Integration**. Expansion to include non-vision sensors (Ultrasonic, IoT) for multimodal situational awareness.

### Progress (rough)

- Documentation: 100%
- Code implementation: ~90% (non-model done, model baseline done)
- Real-environment validation: <30%
- Model/Tracker integration: ~60% (baseline adapter + IOU tracker done; accuracy pending)

### Phased Roadmap

Phase 1) Model/Tracker Adapter

1. Implement EventBuilder adapter for model outputs. (done)
2. Verify payload mapping against `docs/packs/vision/model_interface.md`. (done)
3. Add smoke tests with sample model outputs. (done)
4. Enable multi-model merge (comma-separated adapters). (done)
5. Add tracker integration or synthetic track_id policy for PERSON. (done, IOU tracker)
6. Add accuracy validation pipeline. (pending)

Phase 2) Real RTSP Validation

1. Validate reconnect/backoff behavior on real devices.
2. Confirm codec/fps/latency constraints.
3. Capture error logs and update RTSP runbook.

Phase 3) Real Backend Validation

1. Validate real POST behavior and retries.
2. Confirm response schema and operational metrics.
3. Finalize snapshot path and public URL contract.

Phase 4) Multimodal Sensor Integration

1. Baseline completed: dedicated `SensorSource` lane + nearest attachment + optional `SENSOR_EVENT`/`FUSED_EVENT`.
2. Next: validate real sensor adapters (ROS2/MQTT/serial) on hardware.
3. Next: tune fusion policy and thresholds per site.

### Project Policy Decisions (must decide)

- Event schema finalization (`docs/packs/vision/event_protocol_v0.2.md`)
- Zone coordinate system (pixel 기준 여부)
- RTSP stream spec (resolution, fps, codec, auth)
- Snapshot path/public URL contract
- Model class taxonomy and severity policy (`docs/packs/vision/model_class_taxonomy.md`)
- Hardware target (GPU/Jetson/CPU) and performance targets (FPS/latency)

### References

- Architecture/design: `docs/legacy/design/pipeline_design.md`
- Runtime spec: `docs/legacy/specs/legacy_pipeline_spec.md`
- Model interface: `docs/packs/vision/model_interface.md`
- Ops runbook: `docs/legacy/ops/ops_runbook.md`

### Code Mapping

- Progress logs: `docs/progress/progress_log.md`
- Implementation checklist: `docs/progress/implementation_checklist.md`

## 한국어

## 진행 현황 (2026-02-08 기준)

### 최종 목표

실장비 RTSP를 다중 카메라로 수집하고, 모델/트래커 추론 결과를 계약에 맞춰 백엔드로 전송하며, 안정적인 운영/관측/런북까지 갖춘 파이프라인을 구축한다.

### 목표 결과

1) 실장비 RTSP 안정성/재연결/처리량 검증 완료.
2) 실제 백엔드 연동 E2E 검증 완료.
3) 모델/트래커 연동 및 이벤트 계약 준수.
4) 운영 인수인계 가능한 런북 완성.
5) 모델 클래스 분류 정책 확정 및 프로토콜 반영.
6) 정확도 검증 기준 및 기준 성능 확정.

### 모델 범위(초안)

1) 필수 탐지: 사람, 침입, 위험구역 진입.
2) 선택 탐지(2단계 이후): PPE, 자세, 연기, 화재, 위험상황.
3) v0.2 목록 외 클래스는 프로토콜 업데이트가 필요.

### 가정 / 결정 필요 사항

1) 실행 하드웨어 미정(GPU/Jetson/CPU).
2) 해상도/FPS/지연 목표 미정.
3) 예산 목표: 약 100만원(초안).
4) 클래스 분류와 severity 정책은 프로젝트 정책 확정 필요 (`docs/packs/vision/model_class_taxonomy.md`).
5) 라벨링 정책/학습 리포트 포맷은 ops 문서 기준으로 최종 확인 필요.

### 완료

- 파이프라인 모듈화 (Source/Sampler/Builder/Emitter/Core)
- 파일 기반 ingest + 더미 이벤트 생성
- 모델 어댑터 인터페이스 + 기준 어댑터(YOLO/ONNX)
- 다중 모델 병합(콤마 구분 어댑터)
- Zones & Rules 연동 (zone 로드, rule_point, inside 판정)
- 이벤트 중복 억제 (cooldown + severity override)
- 스냅샷 저장 (경로 생성/저장/public 매핑)
- 관측성 (metrics/heartbeat + json/plain 로깅)
- 설정 검증 + env override + dev/prod 프로필
- RTSP 안정화 로직 (재연결/백오프/타임아웃, read 실패 시 파이프라인 유지)
- 테스트 (unit + integration + regression + RTSP E2E host/docker) 통과
- Docker 패키징 (Dockerfile, entrypoint)
- 파일 소스 무한 루프(`--loop`) + 코어 FPS 제어(Throttling) 로직 구현

### 남은 작업 (완성 조건)

1) **모델/트래커 연동**. 기준 어댑터 + IOU 트래커 완료, 정확도 검증이 남아 있음.
2) **RTSP 실환경 검증**. 실장비 스트림에서 reconnect/timeout 동작 확인.
3) **실제 백엔드 검증**. 실제 POST 성공/실패/타임아웃 정책 검증.
4) **스냅샷 운영 경로 확정**. 운영 환경 스냅샷 경로/권한 확인.
5) **운영 문서 보강**. 운영 문서 보강(실운영 기준).
6) **멀티 센서 연동**. 시각 외 센서(초음파, IoT)를 결합한 멀티모달 상황 인지 능력 확장.

### 진행률(대략)

- 문서화: 100%
- 코드 구현: 90% 내외 (비모델 완료, 모델 기준 어댑터 완료)
- 실환경 검증: 30% 미만
- 모델/트래커 연동: 60% 내외 (기준 어댑터 + IOU 트래커 완료, 정확도 보류)

### 단계별 로드맵

Phase 1) 모델/트래커 어댑터

1. Implement EventBuilder adapter for model outputs. (완료)
2. `docs/packs/vision/model_interface.md` 기준으로 매핑 검증 (완료)
3. 샘플 모델 출력 기반 스모크 테스트 추가 (완료)
4. 다중 모델 병합(콤마 구분 어댑터) 지원 (완료)
5. 트래커 연동 또는 PERSON 합성 track_id 정책 정리 (IOU 기준 완료)
6. 정확도 검증 파이프라인 추가 (보류)

Phase 2) 실장비 RTSP 검증

1. 실장비에서 reconnect/backoff 동작 검증
2. 코덱/fps/지연 제약 확인
3. 에러 로그 정리 및 RTSP 런북 갱신

Phase 3) 실제 백엔드 검증

1. 실제 POST 성공/실패/재시도 정책 검증
2. 응답 스키마 및 운영 메트릭 확인
3. 스냅샷 경로/공개 URL 계약 확정

Phase 4) 멀티 센서 및 멀티모달 연동

1. 기반 완료: 전용 `SensorSource` 축 + 최근 패킷 주입 + 선택 `SENSOR_EVENT`/`FUSED_EVENT`.
2. 다음 단계: 실장비에서 ROS2/MQTT/serial 센서 어댑터 검증.
3. 다음 단계: 현장별 fusion 정책/임계값 튜닝.

### 프로젝트 정책 확정 항목(필수)

- 이벤트 스키마 확정 (`docs/packs/vision/event_protocol_v0.2.md`)
- zone 좌표 기준(픽셀 좌표 여부)
- RTSP 스트림 규격(해상도, fps, 코덱, 인증)
- 스냅샷 경로/공개 URL 계약
- 모델 클래스 분류 및 severity 정책 (`docs/packs/vision/model_class_taxonomy.md`)
- 하드웨어 타깃(GPU/Jetson/CPU)과 성능 목표(FPS/지연)

## 참고

- 아키텍처/설계: `docs/legacy/design/pipeline_design.md`
- 실행 스펙: `docs/legacy/specs/legacy_pipeline_spec.md`
- 모델 인터페이스: `docs/packs/vision/model_interface.md`
- 운영 런북: `docs/legacy/ops/ops_runbook.md`

## 코드 매핑

- 진행 로그: `docs/progress/progress_log.md`
- 구현 체크리스트: `docs/progress/implementation_checklist.md`
