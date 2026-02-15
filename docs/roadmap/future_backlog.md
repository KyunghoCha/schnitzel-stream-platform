# Future Backlog

Last updated: 2026-02-15

## English

## Purpose

This document holds candidate work that is **not yet committed** into execution steps.
Once an item gets schedule/owner/DoD, move it into `docs/roadmap/execution_roadmap.md`.

## Intake Rules

- Each backlog item must define: problem, expected value, risk.
- No item in this file is considered `NOW` or `NEXT` by default.
- Historical plans and completed sub-plans must live under `legacy/docs/archive/roadmap_legacy/`.

## Candidate Backlog

| ID | Theme | Problem | Candidate Direction |
|---|---|---|---|
| B1 | Cycle Runtime | Strict DAG works, but feedback-loop workloads need controlled cycles. | Delay/state-gated cycle semantics and runtime safeguards. |
| B2 | Distributed Graph | Single-process runtime is simple but limits cluster-scale execution. | Transport lanes + remote worker protocol + controller contracts. |
| B3 | Orchestration | Multi-instance lifecycle control is external/manual today. | Optional orchestrator model (health, restart, placement, rollout). |
| B4 | Binary Portability | `file`-based payload refs are host-local. | Object-store/URI-backed refs (`http/s3` style) with lifecycle policy. |
| B5 | UX Layer | Graph authoring/execution UX is still CLI-heavy. | Guided CLI profiles and/or lightweight graph editor. |
| B6 | Plugin SDK | Plugin authoring is possible but onboarding cost is non-trivial. | Templates, validation scaffolds, and compatibility test kit. |
| B7 | Security/Governance | Mixed edge environments need stricter trust boundaries. | Plugin signing policy, secret handling conventions, audit hooks. |

## Promotion Criteria (Backlog -> Execution)

Promote only when all conditions are met:
1. Clear operational pain exists in current users.
2. Scope is bounded for one step in execution roadmap.
3. Success criteria are testable.
4. Owner and review path are defined.

---

## 한국어

## 목적

이 문서는 아직 실행 단계로 확정되지 않은 후보 작업을 보관한다.
일정/담당/DoD가 확정되면 `docs/roadmap/execution_roadmap.md`로 승격한다.

## 인입 규칙

- 각 백로그 항목은 문제/기대효과/리스크를 정의해야 한다.
- 이 문서의 항목은 기본적으로 `NOW`/`NEXT`가 아니다.
- 완료된 하위 계획/역사 문서는 `legacy/docs/archive/roadmap_legacy/`에 둔다.

## 후보 백로그

| ID | 주제 | 문제 | 후보 방향 |
|---|---|---|---|
| B1 | Cycle Runtime | strict DAG는 안정적이지만 피드백 루프 워크로드를 제한한다. | Delay/state 게이트 기반 cycle 의미론 + 런타임 안전장치. |
| B2 | Distributed Graph | 단일 프로세스 런타임은 단순하지만 클러스터 확장 한계가 있다. | 전송 레인 + 원격 워커 프로토콜 + 컨트롤러 계약. |
| B3 | Orchestration | 멀티 인스턴스 생명주기 제어가 현재 외부/수동 중심이다. | 선택형 오케스트레이터 모델(헬스/재시작/배치/롤아웃). |
| B4 | Binary Portability | `file` 기반 payload ref는 호스트 로컬에 묶인다. | 오브젝트 스토어/URI 기반 ref(`http/s3` 계열) + 수명주기 정책. |
| B5 | UX Layer | 그래프 작성/실행 UX가 아직 CLI 중심이다. | 가이드형 CLI 프로필 및/또는 경량 그래프 에디터. |
| B6 | Plugin SDK | 플러그인 작성은 가능하지만 온보딩 비용이 높다. | 템플릿/검증 스캐폴딩/호환성 테스트 키트. |
| B7 | Security/Governance | 혼합 엣지 환경에서 신뢰 경계 관리가 부족하다. | 플러그인 서명 정책, 시크릿 처리 규약, 감사 훅. |

## 승격 기준 (Backlog -> Execution)

아래 조건이 모두 만족될 때만 승격한다.
1. 현재 사용자 운영에서 명확한 문제로 확인된다.
2. 실행 로드맵 한 step으로 범위를 고정할 수 있다.
3. 성공 기준이 테스트 가능하다.
4. 담당자와 리뷰 경로가 확정된다.
