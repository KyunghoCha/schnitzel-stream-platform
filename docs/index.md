# AI Docs Index

## English

This folder is the single source of truth for AI pipeline documentation.

### Start Here

- Suggested reading order:
  1. `specs/pipeline_spec.md`
  2. `contracts/protocol.md`
  3. `specs/model_interface.md`
  4. `specs/model_io_samples.md`
  5. `specs/model_class_taxonomy.md`
  6. `design/pipeline_design.md`
  7. `design/multimodal_pipeline_design.md`
  8. `ops/ops_runbook.md`
  9. `ops/ai/model_yolo_run.md`
  10. `ops/ai/model_training_plan.md`
  11. `ops/ai/labeling_guide.md`
  12. `ops/ai/training_report_template.md`
  13. `ops/ai/performance_optimization.md`
  14. `ops/ai/accuracy_validation.md`
  15. `ops/multi_camera_run.md`
  16. `future/future_roadmap.md` (Detailed roadmap)
  17. `progress/roadmap.md` / `progress/progress_log.md`
- `contracts/protocol.md`: Event schema and API contract
- `progress/roadmap.md`: Status and remaining work
- `specs/pipeline_spec.md`: CLI/config behavior
- `design/pipeline_design.md`: Pipeline architecture
- `design/multimodal_pipeline_design.md`: Multimodal (video + sensor) architecture and phased rollout
- `specs/model_interface.md`: Model/Tracker output contract (real-first, mock explicit for tests)
- `specs/model_io_samples.md`: Model adapter I/O samples
- `specs/model_class_taxonomy.md`: Model class taxonomy (draft)
- `ops/ai/model_yolo_run.md`: YOLO baseline integration runbook (demo section included)
- `ops/ai/model_training_plan.md`: Model training plan (data/label/train/eval)
- `ops/ai/labeling_guide.md`: Labeling rules (draft)
- `ops/ai/training_report_template.md`: Training report template (draft)
- `ops/ai/performance_optimization.md`: performance optimization roadmap
- `ops/ai/accuracy_validation.md`: accuracy validation guide
- `progress/implementation_checklist.md`: Implementation checklist

### Single Source Of Truth

- Event schema: `contracts/protocol.md`
- Model/Tracker contract: `specs/model_interface.md`
- Runtime behavior: `specs/pipeline_spec.md`

### Folders

- `contracts/`: schema/protocol contracts and policy notes
- `specs/`: runtime/behavior specifications
- `design/`: architecture/design docs
- `ops/`: operations, deployment, troubleshooting
- `progress/`: current status and validation logs
- `implementation/`: design/spec notes by topic (reference)

### Implementation Reading Order

- `implementation/00-overview/` → `implementation/10-rtsp-stability/` → `implementation/20-zones-rules/`
→ `implementation/25-model-tracking/` → `implementation/30-event-dedup/`
- `implementation/40-snapshot/` → `implementation/50-backend-integration/` → `implementation/60-observability/`
→ `implementation/70-config/` → `implementation/80-testing/` → `implementation/90-packaging/`

### Code Mapping

- Entry: `src/ai/pipeline/__main__.py`
- Core: `src/ai/pipeline/core.py`

## 한국어

이 폴더가 AI 파이프라인 문서의 기준입니다.

### 시작 가이드

- 읽는 순서(추천):
  1. `specs/pipeline_spec.md`
  2. `contracts/protocol.md`
  3. `specs/model_interface.md`
  4. `specs/model_io_samples.md`
  5. `specs/model_class_taxonomy.md`
  6. `design/pipeline_design.md`
  7. `design/multimodal_pipeline_design.md`
  8. `ops/ops_runbook.md`
  9. `ops/ai/model_yolo_run.md`
  10. `ops/ai/model_training_plan.md`
  11. `ops/ai/labeling_guide.md`
  12. `ops/ai/training_report_template.md`
  13. `ops/ai/performance_optimization.md`
  14. `ops/ai/accuracy_validation.md`
  15. `ops/multi_camera_run.md`
  16. `future/future_roadmap.md` (상세 로드맵)
  17. `progress/roadmap.md` / `progress/progress_log.md`
- `contracts/protocol.md`: 이벤트 스키마 및 API 계약
- `progress/roadmap.md`: 진행 현황과 남은 작업
- `specs/pipeline_spec.md`: CLI/설정 동작
- `design/pipeline_design.md`: 파이프라인 아키텍처
- `design/multimodal_pipeline_design.md`: 멀티모달(영상+센서) 아키텍처 및 단계별 확장 계획
- `specs/model_interface.md`: 모델/트래커 출력 계약(모크 기반)
- `specs/model_io_samples.md`: 모델 어댑터 입출력 샘플
- `specs/model_class_taxonomy.md`: 모델 클래스 분류(초안)
- `ops/ai/model_yolo_run.md`: YOLO 기준 연동 런북(데모 포함)
- `ops/ai/model_training_plan.md`: 모델 학습 계획(데이터/라벨/학습/평가)
- `ops/ai/labeling_guide.md`: 라벨링 규칙(초안)
- `ops/ai/training_report_template.md`: 학습 리포트 템플릿(초안)
- `ops/ai/performance_optimization.md`: 성능/최적화 로드맵
- `ops/ai/accuracy_validation.md`: 정확도 검증 가이드
- `progress/implementation_checklist.md`: 구현 체크리스트

### 단일 기준(SSOT)

- 이벤트 스키마: `contracts/protocol.md`
- 모델/트래커 계약: `specs/model_interface.md`
- 런타임 동작: `specs/pipeline_spec.md`

### 폴더 안내

- `contracts/`: 스키마/프로토콜 계약 및 정책 노트
- `specs/`: 실행/동작 스펙
- `design/`: 설계 문서
- `ops/`: 운영/배포/트러블슈팅
- `progress/`: 진행 현황/검증 로그
- `implementation/`: 주제별 설계/명세 노트(참고용)

### Implementation 읽는 순서

- `implementation/00-overview/` → `implementation/10-rtsp-stability/` → `implementation/20-zones-rules/`
→ `implementation/25-model-tracking/` → `implementation/30-event-dedup/`
- `implementation/40-snapshot/` → `implementation/50-backend-integration/` → `implementation/60-observability/`
→ `implementation/70-config/` → `implementation/80-testing/` → `implementation/90-packaging/`

### 코드 매핑

- 엔트리: `src/ai/pipeline/__main__.py`
- 코어: `src/ai/pipeline/core.py`
