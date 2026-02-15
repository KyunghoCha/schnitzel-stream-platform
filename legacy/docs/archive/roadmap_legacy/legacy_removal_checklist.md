# Legacy Removal Checklist (P4.5)

Last updated: 2026-02-15

## English

### Purpose

Define a safe, auditable checklist for removing legacy runtime from `main`.

### Modes

- Standard mode: remove legacy after the deprecation window (>= 90 days after `P4.3`; earliest date: 2026-05-15).
- Owner override mode: remove earlier only when this checklist is fully satisfied and approved.

### Scope of Removal

- `legacy/ai/**`
- `src/ai/**` shim
- `configs/graphs/legacy_pipeline.yaml`
- `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- related references in docs/tests/CI

### Required Checks (Must Pass)

1. Runtime safety
   - All production/default paths run on v2 graphs only.
   - No required operational path depends on v1 job graph.

2. Import boundary
   - `schnitzel_stream.*` has zero direct `ai.*` imports.
   - plugin policy no longer requires `ai.` allowlist as default.

3. Test/validation baseline
   - compile check passes: `python3 -m compileall -q src tests`
   - CI green on supported matrix + no-docker-smoke lane.
   - v2 golden/regression tests cover at least one end-to-end event path.

4. Documentation and migration
   - command reference no longer recommends v1 legacy execution.
   - docs clearly mark legacy removal date and migration path.

5. Rollback readiness
   - create pre-removal tag (example: `pre-p45-legacy-removal-YYYYMMDD`).
   - keep rollback instructions in release notes/PR description.

### Owner Override Approval Record

When using owner override mode, record the following in PR description:
- approval timestamp (UTC)
- approver handle
- checklist evidence links (CI run + key test logs)
- rollback tag name

### Completion Record

- Status: completed (owner override path)
- Date: 2026-02-15 (UTC)
- Result: legacy runtime removed from `main` (`legacy/ai/**`, `src/ai/**`, v1 graph/job path)

---

## 한국어

### 목적

`main`에서 레거시 런타임을 제거할 때, 안전하고 추적 가능한 체크리스트를 정의한다.

### 모드

- 표준 모드: deprecation window 이후 삭제(`P4.3` 이후 90일 경과, 최단 삭제일: 2026-05-15).
- owner override 모드: 이 체크리스트를 전부 통과하고 승인된 경우 조기 삭제 허용.

### 삭제 범위

- `legacy/ai/**`
- `src/ai/**` shim
- `configs/graphs/legacy_pipeline.yaml`
- `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 관련 docs/tests/CI 참조

### 필수 체크 (모두 통과해야 함)

1. 런타임 안전성
   - 모든 운영/기본 경로가 v2 그래프 기준으로 동작해야 한다.
   - v1 job 그래프 의존 운영 경로가 없어야 한다.

2. import 경계
   - `schnitzel_stream.*`에서 `ai.*` 직접 import가 0이어야 한다.
   - 플러그인 정책 기본 allowlist에서 `ai.` 의존이 제거되어야 한다.

3. 테스트/검증 기준
   - compile 체크 통과: `python3 -m compileall -q src tests`
   - 지원 CI 매트릭스 + no-docker-smoke lane green.
   - v2 golden/regression 테스트가 최소 1개 이상 E2E 이벤트 경로를 커버.

4. 문서/마이그레이션
   - 명령어 문서에서 v1 레거시 실행 권장이 제거되어야 한다.
   - 레거시 제거 날짜와 마이그레이션 경로가 문서에 명확해야 한다.

5. 롤백 준비
   - 삭제 직전 태그 생성(예: `pre-p45-legacy-removal-YYYYMMDD`).
   - 릴리즈 노트/PR 설명에 롤백 절차를 남긴다.

### Owner Override 승인 기록

owner override 모드를 사용할 때 PR 설명에 아래를 남긴다:
- 승인 시각(UTC)
- 승인자 핸들
- 체크리스트 증빙 링크(CI 실행 + 핵심 테스트 로그)
- 롤백 태그명

### 완료 기록

- 상태: 완료(owner override 경로)
- 일자: 2026-02-15 (UTC)
- 결과: `main`에서 레거시 런타임 제거(`legacy/ai/**`, `src/ai/**`, v1 graph/job 경로)
