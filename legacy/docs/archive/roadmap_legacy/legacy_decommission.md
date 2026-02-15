# Legacy Decommission (P4.1 SSOT)

Last updated: 2026-02-15

## English

Goal: planfully remove the legacy runtime (`legacy/ai/**`, import path `ai.*`) and the v1 (job) graph format, and fully transition to the v2 (node) graph-based platform.

This document is the Phase 4 (`P4.*`) SSOT that defines **when** and **by what criteria** legacy can be removed.

Status:
- `P4.5` is complete on `main` (owner override path was used with checklist evidence).

### What Counts As "Legacy"

- Code: `legacy/ai/**` (plus the `src/ai` shim)
- v1 (job) graph format: `version: 1`
- Legacy v1 graph: `configs/graphs/legacy_pipeline.yaml`
- Phase 0 compatibility job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- Plugin allowlist including the `ai.*` namespace

### Strategy (Strangler, No Big Bang)

1. **Define parity** (`P4.1`): decide what behavior must match, and what is explicitly dropped.
2. **Reach parity with v2** (`P4.2`): cover required operational behavior via v2 graphs + nodes.
   - Wrapping is allowed if needed, but it is temporary. The end goal is removing `ai.*` dependencies.
3. **Cutover** (`P4.3`): switch the default graph to v2 and deprecate v1.
4. **Extract or quarantine** (`P4.4`): keep legacy pinned under `legacy/`, or move it to a separate package/repo.
5. **Delete** (`P4.5`): remove from the main tree after the deprecation window.

### Parity Scope (Baseline)

We do not aim to clone all legacy features. We define a minimum "operational baseline" first.

Baseline candidate (adjustable):
- Input: at least one of file/RTSP/webcam is available as v2
- Processing: sampling/preprocess/model inference/postprocess (tracking/fusion)/policy (Zone/Dedup)/event build
- Output: at least one of backend/file/stdout sinks is available as v2
- Failure/restart: replayability via `at-least-once + idempotency` (Phase 2 durable queue can be used)
- Observability: metrics/health consistent with `docs/contracts/observability.md`

Explicitly out-of-scope initially:
- GUI visualization (debug window)
- All multi-sensor fusion modes
- All model/backend combinations

### Cutover Criteria (Definition of Done)

`P4.3` (default v2 cutover) requires:
- v2 graphs cover the agreed "operational baseline".
- At least one end-to-end "golden" scenario exists as an automated test.
- v1 (job) execution remains runnable, but docs and CLI must clearly mark it as deprecated.

`P4.5` (legacy deletion) requires:
- At least **90 days** have elapsed after `P4.3` is merged. (deprecation window)
- On `main`, `schnitzel_stream.*` has **zero** direct imports from `ai.*`.
- There are no internal/external consumers of v1 graphs (or they were moved/isolated via `P4.4`).

Owner override path:
- The 90-day window is the default safety path.
- Earlier removal is allowed only with explicit owner approval and full completion of
  `legacy/docs/archive/roadmap_legacy/legacy_removal_checklist.md`.

### Deprecation Policy (Timeline)

- Never delete legacy immediately.
- The deprecation window is managed by **roadmap events**, not calendar dates.
  - Start: when `P4.3` is merged
  - Earliest deletion: at least 90 days after `P4.3` merge
- Owner override is permitted only with explicit approval + checklist evidence.

### Operational Policy (Until Removed)

- Default policy for `legacy/ai/**` is "freeze" (no new features).
  - Allowed: security/crash/data-loss bug fixes
  - Forbidden: new features, expanding plugin boundaries, adding new config keys

### Open Questions

- How far should "model inference" parity go (ONNX/YOLO/Custom)?
- What is the fixed subset of backend event schema (required vs optional fields)?
- Do we include multi-camera/multi-sensor parity in Phase 4, or defer it?

---

## 한국어

목표: `legacy/ai/**` 레거시 런타임(import 경로: `ai.*`)과 v1(job) 그래프 포맷을 **계획적으로 제거**하고, v2(node) 그래프 기반 플랫폼으로 완전히 전환한다.

이 문서는 Phase 4(`P4.*`)의 SSOT이며, “언제/무엇을 기준으로 레거시를 없애는가”를 정의한다.

상태:
- `P4.5`는 `main`에서 완료되었고, owner override + 체크리스트 증빙 경로를 사용했다.

### 레거시 정의(무엇이 레거시인가)

- 코드: `legacy/ai/**` (+ `src/ai` shim)
- v1(job) 그래프 포맷: `version: 1`
- 레거시 그래프(v1): `configs/graphs/legacy_pipeline.yaml`
- Phase 0 호환 job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 플러그인 allowlist에 포함된 `ai.*` 네임스페이스

### 전략 (Strangler, No Big Bang)

1. **패리티 정의** (`P4.1`): 어떤 동작을 “같다”고 볼지, 무엇을 명시적으로 버릴지 결정한다.
2. **v2로 패리티 달성** (`P4.2`): v2 그래프 + 노드로 운영에 필요한 행동을 커버한다.
   - 필요하면 래핑을 허용하되, 래핑은 임시이며 최종 목표는 `ai.*` 의존성 제거다.
3. **전환(Cutover)** (`P4.3`): 기본 그래프를 v2로 바꾸고 v1을 deprecate 한다.
4. **추출/격리** (`P4.4`): 레거시를 별도 패키지/리포로 빼거나, `legacy/` 아래에 고정(pinned)해 내부 전용으로 격리한다.
5. **삭제(Delete)** (`P4.5`): deprecation window 종료 후 main tree에서 제거한다.

### 패리티 범위 (Baseline)

레거시 기능을 전부 복제하는 것이 아니라, “운영에 필요한 최소”를 먼저 정의한다.

Baseline 후보(조정 가능):
- 입력: 파일/RTSP/Webcam 중 최소 1개는 v2로 제공
- 처리: 샘플링/전처리/모델 추론/후처리(추적/퓨전)/정책(Zone/Dedup)/이벤트 빌드
- 출력: backend/file/stdout 중 최소 1개 sink를 v2로 제공
- 장애/재시작: `at-least-once + idempotency` 기반 replay 가능성(Phase 2 durable queue 활용 가능)
- 관측: `docs/contracts/observability.md` 수준의 metrics/health 일관성

명시적으로 “초기엔 안 한다” 후보:
- GUI 시각화(디버그 window)
- 멀티 센서 퓨전의 모든 모드
- 모든 모델/백엔드 조합

### 전환 기준 (Definition of Done)

`P4.3`(default v2 전환) 기준:
- v2 그래프가 **운영 baseline**을 커버한다(합의된 Parity Scope 기준).
- 최소 1개의 end-to-end “golden” 시나리오가 자동화 테스트로 존재한다.
- v1(job) 실행은 유지하되, 문서와 CLI에서 deprecation이 명시된다.

`P4.5`(legacy 삭제) 기준:
- `P4.3`가 **머지된 이후 최소 90일**이 지났다. (deprecation window)
- `main` 기준으로 `schnitzel_stream.*`에서 `ai.*` 직접 import가 0이다.
- v1 그래프를 사용하는 내부/외부 소비자가 없다(또는 `P4.4`로 별도 패키지로 격리/이관됨).

Owner override 경로:
- 90일 규칙은 기본 안전 경로입니다.
- 조기 삭제는 owner의 명시적 승인 + `legacy/docs/archive/roadmap_legacy/legacy_removal_checklist.md`
  전 항목 통과 시에만 허용합니다.

### 디프리케이션 정책 (Timeline)

- 레거시 삭제는 **절대 즉시 삭제하지 않는다**.
- deprecation window는 “절대 날짜”가 아니라 **로드맵 이벤트 기준**으로 관리한다.
  - 시작: `P4.3` 머지 시점
  - 삭제 가능 최단: `P4.3` 머지 이후 최소 90일 경과
- owner override는 승인 기록 + 체크리스트 증빙이 있을 때만 허용한다.

### 운영 정책 (삭제 전까지)

- `legacy/ai/**`는 “기능 추가 금지(Freeze)”가 기본이다.
  - 허용: 보안/크래시/데이터 손실 버그 픽스
  - 금지: 신규 기능/새 플러그인 경계 확장/새 설정 키 추가

### 미해결 질문

- Baseline parity에서 “모델 추론”을 어디까지 포함할지(ONNX/YOLO/Custom)
- backend event schema의 고정 범위(필수 필드/optional 필드)
- multi-camera/multi-sensor를 Phase 4에 포함할지, 이후로 미룰지
