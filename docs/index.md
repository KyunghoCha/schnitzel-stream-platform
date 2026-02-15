# Schnitzel Stream Docs Index

## English

This folder is the single source of truth for `schnitzel-stream-platform` documentation.

Phase 0 note:
- Entrypoint is `python -m schnitzel_stream`.
- The legacy AI runtime remains under `ai.*` modules and is executed through a Phase 0 job.

### Start Here (Platform Pivot)

- Suggested reading order:
  1. `roadmap/strategic_roadmap.md` (Vision / target architecture)
  2. `roadmap/migration_plan_phase0.md` (What we are changing now)
  3. `roadmap/execution_roadmap.md` (Execution SSOT: plan + status)
  4. `roadmap/legacy_decommission.md` (Phase 4: when/how legacy is removed)
  5. `design/architecture_2.0.md` (Provisional architecture spec)
  6. `implementation/90-packaging/entrypoint/design.md` (Entrypoint design)
  7. `implementation/90-packaging/support_matrix.md` (Edge support matrix, provisional)
  8. `legacy/specs/legacy_pipeline_spec.md` (Legacy pipeline behavior, executed via `schnitzel_stream`)
  9. `contracts/stream_packet.md` (Internal node-to-node contract, provisional)
  10. `contracts/observability.md` (Metrics/health contract, provisional)
  11. `packs/vision/event_protocol_v0.2.md` (Event schema / transport contract)

### Legacy AI Pipeline Deep Dive (Optional)

- `legacy/design/pipeline_design.md`: legacy pipeline architecture
- `legacy/design/multimodal_pipeline_design.md`: legacy multimodal (video + sensor) design and rollout
- `packs/vision/model_interface.md`: model adapter I/O contract
- `packs/vision/model_class_taxonomy.md`: class taxonomy (draft)
- `legacy/ops/ops_runbook.md`: operations runbook
- `legacy/ops/multi_camera_run.md`: multi-camera operations

### Single Source Of Truth

- Platform pivot: `roadmap/strategic_roadmap.md`, `roadmap/migration_plan_phase0.md`, `design/architecture_2.0.md`
- Execution plan/status: `roadmap/execution_roadmap.md`
- Runtime behavior (legacy job): `legacy/specs/legacy_pipeline_spec.md`
- Node-to-node contract: `contracts/stream_packet.md`
- Observability contract: `contracts/observability.md`
- Event schema: `packs/vision/event_protocol_v0.2.md`
- Model/Tracker contract: `packs/vision/model_interface.md`

### Folders

- `contracts/`: schema/protocol contracts and policy notes
- `specs/`: runtime/behavior specifications
- `design/`: architecture/design docs
- `ops/`: operations, deployment, troubleshooting
- `legacy/`: quarantined legacy-only docs (v1 runtime lineage)
- `packs/`: optional domain packs (vision, sensors, etc)
- `roadmap/`: strategic/execution roadmap and backlog
- `progress/`: current status and validation logs
- `implementation/`: design/spec notes by topic (reference)

### Code Mapping

- Entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Default graph spec (v2): `configs/graphs/dev_vision_e2e_mock_v2.yaml`
- Legacy graph spec (v1): `configs/graphs/legacy_pipeline.yaml`
- Phase 0 legacy job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- Legacy pipeline core: `legacy/ai/pipeline/core.py` (import path remains `ai.*`)

## 한국어

이 폴더는 `schnitzel-stream-platform` 문서의 단일 기준(SSOT)입니다.

Phase 0 참고:
- 엔트리포인트는 `python -m schnitzel_stream` 입니다.
- 레거시 AI 런타임은 `ai.*` 모듈로 유지되며, Phase 0 job을 통해 실행됩니다.

### 시작 가이드 (플랫폼 피벗)

- 읽는 순서(추천):
  1. `roadmap/strategic_roadmap.md` (비전 / 목표 아키텍처)
  2. `roadmap/migration_plan_phase0.md` (지금 바꾸는 내용)
  3. `roadmap/execution_roadmap.md` (실행 SSOT: 계획 + 상태)
  4. `roadmap/legacy_decommission.md` (Phase 4: 레거시 제거 기준/일정)
  5. `design/architecture_2.0.md` (아키텍처 명세, 잠정)
  6. `implementation/90-packaging/entrypoint/design.md` (엔트리포인트 설계)
  7. `implementation/90-packaging/support_matrix.md` (엣지 지원 매트릭스, 잠정)
  8. `legacy/specs/legacy_pipeline_spec.md` (레거시 파이프라인 동작, `schnitzel_stream`로 실행)
  9. `contracts/stream_packet.md` (노드 간 내부 계약, 잠정)
  10. `contracts/observability.md` (메트릭/헬스 계약, 잠정)
  11. `packs/vision/event_protocol_v0.2.md` (이벤트 스키마/전송 계약)

### 레거시 AI 파이프라인 상세 (선택)

- `legacy/design/pipeline_design.md`: 레거시 파이프라인 설계
- `legacy/design/multimodal_pipeline_design.md`: 레거시 멀티모달(영상+센서) 설계/확장 계획
- `packs/vision/model_interface.md`: 모델 어댑터 I/O 계약
- `packs/vision/model_class_taxonomy.md`: 클래스 분류(초안)
- `legacy/ops/ops_runbook.md`: 운영 런북
- `legacy/ops/multi_camera_run.md`: 멀티 카메라 운영

### 단일 기준(SSOT)

- 플랫폼 피벗: `roadmap/strategic_roadmap.md`, `roadmap/migration_plan_phase0.md`, `design/architecture_2.0.md`
- 실행 계획/상태: `roadmap/execution_roadmap.md`
- 런타임 동작(레거시 job): `legacy/specs/legacy_pipeline_spec.md`
- 노드 간 계약: `contracts/stream_packet.md`
- 관측 가능성 계약: `contracts/observability.md`
- 이벤트 스키마: `packs/vision/event_protocol_v0.2.md`
- 모델/트래커 계약: `packs/vision/model_interface.md`

### 폴더 안내

- `contracts/`: 스키마/프로토콜 계약 및 정책 노트
- `specs/`: 실행/동작 스펙
- `design/`: 설계 문서
- `ops/`: 운영/배포/트러블슈팅
- `legacy/`: 격리된 레거시 전용 문서(v1 런타임 계보)
- `packs/`: 옵션 도메인 팩(vision, sensors 등)
- `roadmap/`: 전략/실행 로드맵 및 백로그
- `progress/`: 진행 현황/검증 로그
- `implementation/`: 주제별 설계/명세 노트(참고)

### 코드 매핑

- 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 기본 그래프 스펙(v2): `configs/graphs/dev_vision_e2e_mock_v2.yaml`
- 레거시 그래프 스펙(v1): `configs/graphs/legacy_pipeline.yaml`
- Phase 0 레거시 job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 레거시 파이프라인 코어: `legacy/ai/pipeline/core.py` (import 경로는 `ai.*` 유지)
