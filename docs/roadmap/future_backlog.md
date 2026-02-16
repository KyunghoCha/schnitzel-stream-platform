# Future Backlog

Last updated: 2026-02-16

## English

## Purpose

This document holds candidate work that is **not yet committed** into execution steps.
Once an item gets schedule/owner/DoD, move it into `docs/roadmap/execution_roadmap.md`.

## Intake Rules

- Each backlog item must define: problem, expected value, risk.
- No item in this file is considered `NOW` or `NEXT` by default.
- Historical plans and completed sub-plans must be tracked via git history/tag (`pre-legacy-purge-20260216`).

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
| B8 | Graph Profiles | Operators repeatedly tune similar runtime knobs per deployment class. | Standardized run profiles (`edge_low_power`, `server_realtime`, `offline_batch`). |
| B9 | Policy Pack | Retry/timeout/drop/backpressure behavior is fragmented across node choices. | Policy plugins that can be swapped without editing graph topology. |
| B10 | Replay Inspector | Durable queue replay debugging is slow and manual. | Time/key/node-filtered inspector for queue trace + selective replay. |
| B11 | Contract Diff Gate | Payload contract drift can silently break downstream nodes. | CI gate that diffs payload schema and blocks unsafe compatibility breaks. |
| B12 | Plugin Compatibility Matrix | Users cannot quickly know plugin support by OS/Python/dependency set. | Automated compatibility report generation per pack/plugin. |
| B13 | Reliability Chaos Kit | Failure handling paths are under-tested compared to happy path. | Fault injection pack (network cut, delayed ack, disk pressure, restart storm). |
| B14 | SLO Report Pack | Performance quality is hard to compare over builds/releases. | Automated p95/p99 latency, drop rate, replay rate, recovery-time summaries. |
| B15 | Dead Letter Queue Standard | Repeated poison events are mixed into normal durable flow. | Standard DLQ contract + tooling for quarantine and controlled re-drive. |

## Priority Seed Pack (Thread-Excluded)

For next promotion discussion, these are the highest leverage candidates:
1. `B9` Policy Pack: maximizes operator control with minimal core-runtime change.
2. `B10` Replay Inspector: shortens incident debugging and improves trust in durability.
3. `B13` Reliability Chaos Kit: validates behavior under edge failures before field rollout.

## Foundation Hook (Post-P12)

- `P12` foundation keeps process-graph schema generic (`links[]`) while enforcing strict `1:1` channel cardinality in validator rules.
- Planned expansion path (candidate for `P13`): relax validator cardinality to support `N:N` channels without breaking spec format.
- Open design constraint: define ack ownership and replay dedup semantics before enabling multi-producer or multi-consumer channels.

## Promotion Criteria (Backlog -> Execution)

Promote only when all conditions are met:
1. Clear operational pain exists in current users.
2. Scope is bounded for one step in execution roadmap.
3. Success criteria are testable.
4. Owner and review path are defined.

---

## 한국어

## 문서 목적

이 문서는 아직 일정이 확정되지 않은 **후보 과제 저장소**다.
일정, 담당자, 완료 기준이 잡히면 `docs/roadmap/execution_roadmap.md`로 옮긴다.

## 등록 규칙

- 항목마다 문제, 기대효과, 리스크를 반드시 적는다.
- 이 문서에 있는 항목은 기본적으로 `NOW`나 `NEXT`가 아니다.
- 끝난 계획/과거 이력은 git 이력/태그(`pre-legacy-purge-20260216`)로 관리한다.

## 후보 과제

| ID | 주제 | 문제 | 검토 방향 |
|---|---|---|---|
| B1 | 순환 그래프 런타임 | strict DAG만으로는 피드백 루프 계열 워크로드를 다루기 어렵다. | delay/state 게이트 기반 순환 실행 모델과 안전장치 설계 |
| B2 | 분산 그래프 실행 | 단일 프로세스 런타임은 단순하지만 클러스터 확장에 한계가 있다. | 전송 레인 분리, 원격 워커 프로토콜, 제어 계약 정립 |
| B3 | 오케스트레이션 | 다중 인스턴스 운용이 아직 수동 절차에 많이 의존한다. | 선택형 오케스트레이터(헬스/재시작/배치/롤아웃) 도입 |
| B4 | 바이너리 이식성 | `file` 기반 payload ref는 단일 호스트에 종속된다. | 오브젝트 스토어/URI 기반 ref(`http/s3` 계열) 확장 |
| B5 | 사용성 계층 | 그래프 작성과 실행 경험이 CLI 중심이라 진입 장벽이 있다. | 가이드형 CLI 프로필, 경량 그래프 편집 도구 검토 |
| B6 | 플러그인 SDK | 플러그인 작성 자체는 가능하지만 초기 진입 비용이 높다. | 템플릿, 검증 스캐폴딩, 호환성 테스트 키트 제공 |
| B7 | 보안/거버넌스 | 이기종 엣지 환경에서 신뢰 경계와 감사 체계가 약하다. | 플러그인 서명 정책, 시크릿 규약, 감사 훅 정리 |
| B8 | 그래프 프로필 | 배포 유형이 달라도 비슷한 런타임 튜닝을 매번 반복한다. | `edge_low_power`, `server_realtime`, `offline_batch` 같은 표준 실행 프로필 제공 |
| B9 | 정책 팩 | 재시도/타임아웃/드롭/백프레셔 정책이 노드 선택에 분산되어 운영 제어가 어렵다. | 그래프 토폴로지 수정 없이 교체 가능한 정책 플러그인 도입 |
| B10 | 리플레이 인스펙터 | durable 큐 문제를 추적/재현하는 절차가 수동이라 시간이 오래 걸린다. | 시간/키/노드 필터 기반 조회와 선택 재생 도구 제공 |
| B11 | 계약 차이 게이트 | payload 계약이 바뀌어도 하위 호환 깨짐이 늦게 발견된다. | CI에서 스키마 차이 비교로 위험 변경을 사전 차단 |
| B12 | 플러그인 호환성 매트릭스 | OS/Python/의존성 조합별 지원 여부를 사용자가 빠르게 확인하기 어렵다. | pack/plugin 단위 자동 호환성 리포트 생성 |
| B13 | 신뢰성 카오스 키트 | 정상 경로 대비 장애 경로 회귀 검증이 약하다. | 네트워크 단절/ACK 지연/디스크 압박/재시작 폭주 주입 테스트 팩 |
| B14 | SLO 리포트 팩 | 빌드/릴리즈 간 실제 성능 품질 비교가 어렵다. | p95/p99 지연, drop율, replay율, 복구 시간 자동 요약 |
| B15 | DLQ 표준화 | 독성 이벤트가 일반 durable 흐름에 섞여 재처리 비용이 커진다. | 격리 저장(DLQ) 계약과 안전한 재투입 도구 표준화 |

## 우선 검토 묶음 (스레드 제외)

다음 승격 논의에서 효과가 큰 후보는 아래 3개다.
1. `B9` 정책 팩: 코어 변경을 최소화하면서 운영 제어력을 빠르게 올릴 수 있다.
2. `B10` 리플레이 인스펙터: 장애 분석 시간을 크게 줄이고 durable 신뢰도를 높인다.
3. `B13` 신뢰성 카오스 키트: 실환경 배포 전 극한 상황 회귀를 자동화할 수 있다.

## Foundation 훅 (P12 이후)

- `P12` foundation은 process-graph 스키마를 일반형(`links[]`)으로 유지하고, validator 규칙에서만 strict `1:1` 채널 cardinality를 강제한다.
- `P13` 후보 확장 경로: 스펙 포맷을 깨지 않고 validator cardinality 규칙을 완화해 `N:N` 채널을 지원한다.
- 선결 과제: 멀티 producer/consumer 채널에서 ack ownership과 replay dedup 의미론을 먼저 고정해야 한다.

## 승격 기준 (Backlog -> Execution)

아래 조건이 모두 충족될 때만 실행 로드맵으로 승격한다.
1. 실제 운영에서 재현되는 문제로 확인되었다.
2. 실행 로드맵의 단일 step으로 범위를 고정할 수 있다.
3. 성공 여부를 테스트로 검증할 수 있다.
4. 담당자와 리뷰 경로가 정해졌다.
