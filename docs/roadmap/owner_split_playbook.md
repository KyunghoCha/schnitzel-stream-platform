# Owner Split Playbook (Agent Build Track vs User Research Track)

Last updated: 2026-02-16

## English

## Scope and Boundary

This playbook fixes decision ownership after `P12` completion.

- Runtime baseline remains: in-proc v2 node graph + process-graph foundation validator (`P12`).
- This document separates:
  - implementable engineering work that can be executed without new research decisions
  - research work that must be designed and validated experimentally
- Non-scope:
  - immediate distributed control-plane implementation
  - immediate runtime `N:N` channel execution
  - immediate runtime cycle execution beyond current validator policy

## Execution Status Snapshot

Current step id: `P15.1`

### Agent Track Status (`E-*`)

| Item | Status | Notes |
|---|---|---|
| `E1` | `DONE` | `env_doctor` added and wired into docs/CI path (P15 profile extension in progress) |
| `E2` | `DONE` | no-docker CI gate expanded (`env/docs/tests/procgraph/demo`) |
| `E3` | `DONE` | `demo_pack` schema/failure taxonomy hardened |
| `E4` | `DONE` | static report renderer (`demo_report_view`) added |
| `E5` | `DONE` | scaffold auto-export registration with opt-out shipped |
| `E6` | `DONE` | durable queue boundary/restart regression cases expanded |

### Research Track Status (`R-*`)

| Item | Status | Notes |
|---|---|---|
| `R1` | `BLOCKED_BY_RESEARCH` | requires thesis-grade semantics decisions |
| `R2` | `BLOCKED_BY_RESEARCH` | ack ownership/dedup policy is unresolved |
| `R3` | `BLOCKED_BY_RESEARCH` | runtime cycle safety model not fixed |
| `R4` | `BLOCKED_BY_RESEARCH` | distributed orchestration model not fixed |
| `R5` | `BLOCKED_BY_RESEARCH` | cross-host payload lifecycle model pending |
| `R6` | `BLOCKED_BY_RESEARCH` | security/governance baseline pending |

### Gate Status (`G-*`)

| Gate | Status | Dependency |
|---|---|---|
| `G1` | `BLOCKED_BY_RESEARCH` | `R1` + `R2` |
| `G2` | `BLOCKED_BY_RESEARCH` | `R3` |
| `G3` | `BLOCKED_BY_RESEARCH` | `R4` |
| `G4` | `BLOCKED_BY_RESEARCH` | `R5` + `R6` |

## Agent Build Track (`E-*`)

### `E1` CI and Environment Recovery

- Goal: keep GitHub Actions green and align local/CI reproducibility (conda baseline included).
- Artifacts:
  - CI workflow fixes and verification command matrix updates
  - environment troubleshooting note in active ops docs
- Definition of Done:
  - same command set passes in local and CI lanes
  - failures return deterministic error messages and non-zero status
- Verification commands:
  - `python3 scripts/docs_hygiene.py --strict`
  - `python3 scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0`
  - `python scripts/demo_pack.py --profile ci`
- Risk:
  - dependency drift between local conda and CI runner image

### `E2` Validation Gate Hardening

- Goal: make docs/test/graph checks mandatory at PR boundary.
- Artifacts:
  - CI lane that runs strict docs hygiene + test hygiene + graph validation + demo profile
  - failure triage guidance in command reference
- Definition of Done:
  - pre-merge signal is deterministic (clear fail/pass contract)
  - no silent skip for required checks
- Verification commands:
  - `python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml`
  - `python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml`
- Risk:
  - false negatives from optional dependency gaps

### `E3` Showcase Quality Lock

- Goal: keep professor demo outputs readable and reproducible without changing core semantics.
- Artifacts:
  - stable summary/report format for `scripts/demo_pack.py`
  - explicit failure-code guide linked from ops docs
- Definition of Done:
  - S1/S2/S3 scenario runbook is complete in one guide
  - operator can diagnose failures without reading source
- Verification commands:
  - `python scripts/demo_pack.py --profile ci`
- Risk:
  - hardware variance on webcam path for professor profile

### `E4` Lightweight Visualization (Research-Independent)

- Goal: provide static visualization of demo outputs without full GUI stack.
- Artifacts:
  - converter script from JSON report to Markdown/HTML summary, or equivalent static renderer
  - docs for CI-safe usage
- Definition of Done:
  - visualization output is generated in hardware-free CI profile
  - report includes scenario status and key metrics
- Verification commands:
  - `python scripts/demo_pack.py --profile ci`
  - visualizer command against generated report
- Risk:
  - overextending scope into full frontend implementation

### `E5` Plugin DX Finalization

- Goal: reduce plugin authoring friction for source/node/sink creation.
- Artifacts:
  - improved scaffold output quality
  - validated template examples in guide/docs mapping
- Definition of Done:
  - generated source/node/sink plugin skeletons pass baseline tests
  - authoring flow is reproducible from command reference
- Verification commands:
  - scaffold script command + generated test execution
- Risk:
  - template drift from runtime interfaces

### `E6` Reliability Regression Expansion

- Goal: strengthen outage/restart/backlog regression coverage.
- Artifacts:
  - additional tests for durable queue boundary conditions
  - explicit pass/fail criteria for replay and ack flows
- Definition of Done:
  - outage class scenarios are represented in automated tests
  - regressions are caught before merge
- Verification commands:
  - `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
- Risk:
  - flaky tests under constrained CI resources

## User Research Track (`R-*`)

### `R1` `N:N` Channel Semantics

- Research question: who owns message progression in multi-producer/multi-consumer channels?
- Minimum experiments:
  - compare 1:2, 2:1, 2:2 topologies for replay delay and duplication behavior
- Success criteria:
  - semantics document with explicit ownership and ordering guarantees
- Deliverable:
  - channel semantics decision doc
- Unblocks:
  - `G1`

### `R2` Ack Ownership and Dedup Policy

- Research question: what is the dedup key scope and ack authority boundary?
- Minimum experiments:
  - conflicting keys, delayed ack, duplicate delivery recovery
- Success criteria:
  - correctness contract that defines loss/duplication boundaries
- Deliverable:
  - ack/dedup contract doc
- Unblocks:
  - `G1`

### `R3` Runtime Cycle Execution Model

- Research question: what loop model is safe beyond validator-only allowances?
- Minimum experiments:
  - delay/observer loop stability and stop-condition behavior
- Success criteria:
  - safety spec with stop conditions and overload guardrails
- Deliverable:
  - cycle runtime safeguards spec
- Unblocks:
  - `G2`

### `R4` Process-Graph Execution and Orchestration

- Research question: how to scale from local multi-process execution to distributed orchestration?
- Minimum experiments:
  - local multi-process baseline -> remote bridge trial
- Success criteria:
  - staged execution model with failure recovery policy
- Deliverable:
  - process-graph execution roadmap (research-track)
- Unblocks:
  - `G3`

### `R5` Cross-Host `payload_ref` Strategy

- Research question: how should lifecycle and access control work for URI/object-store refs?
- Minimum experiments:
  - local file ref vs network/object-store ref performance and recovery comparison
- Success criteria:
  - portability v2 proposal with lifecycle rules
- Deliverable:
  - payload portability v2 proposal
- Unblocks:
  - `G4`

### `R6` Security and Governance Baseline

- Research question: what minimum trust policy is required for plugin execution?
- Minimum experiments:
  - malicious plugin and secret-handling abuse scenarios
- Success criteria:
  - enforceable baseline for signing, secret handling, and audit hooks
- Deliverable:
  - security/governance baseline spec
- Unblocks:
  - `G4`

## Gate Matrix (`G-*`)

| Gate | Blocked Until | Blocked Implementation |
|---|---|---|
| `G1` | `R1` + `R2` complete | runtime `N:N` channel execution |
| `G2` | `R3` complete | runtime cycle execution enablement |
| `G3` | `R4` complete | distributed orchestrator/control-plane implementation |
| `G4` | `R5` + `R6` complete | default cross-host binary payload enablement |

## Working Contract

### Reporting Format

- Each update includes:
  - step id (`P13.1` until SSOT changes)
  - item id (`E*` or `R*`)
  - status code (`READY`, `BLOCKED_BY_RESEARCH`, `DONE`)
  - evidence path (test log, doc path, CI run reference)

### Status Code Rules

- `READY`: can be executed without unresolved research decision
- `BLOCKED_BY_RESEARCH`: implementation intentionally paused until required `R*` outputs exist
- `DONE`: completed with evidence and mapped docs updated

### Sync Rules

- If any `E*` item changes scope, update in the same change set:
  - `docs/roadmap/execution_roadmap.md`
  - `docs/progress/current_status.md`
  - `docs/reference/document_inventory.md`
- If any `R*` item reaches a decision, reflect gate impact in:
  - `docs/roadmap/future_backlog.md`
  - `docs/roadmap/execution_roadmap.md` (if promoted)

### Assumptions and Defaults

- Base state is `P12` completion with in-proc runtime unchanged.
- P13 execution-completion cycle is complete for implementation-only items (`E1`~`E6`).
- Calendar dates are not used as hard gates; gate satisfaction order is primary.
- Full GUI stack is out-of-scope before research gates; static visualization is preferred first.
- No gate-blocked implementation starts before required research deliverables are accepted.

---

## 한국어

## 범위와 경계

이 문서는 `P12` 완료 이후 작업의 책임 경계를 고정하기 위한 실행 플레이북이다.

- 런타임 기준선은 유지한다:
  - in-proc v2 노드 그래프
  - process-graph foundation validator (`P12`)
- 이 문서는 다음 두 축을 분리한다:
  - 연구 의사결정 없이 바로 실행 가능한 구현 작업
  - 실험/검증이 선행되어야 하는 연구 작업
- 비범위:
  - 즉시 분산 컨트롤 플레인 구현
  - 즉시 `N:N` 채널 런타임 실행
  - 현재 validator 정책을 넘는 즉시 루프 실행 허용

## 실행 상태 스냅샷

현재 step id: `P15.1`

### Agent 트랙 상태 (`E-*`)

| 항목 | 상태 | 메모 |
|---|---|---|
| `E1` | `DONE` | `env_doctor` 추가 및 문서/CI 경로 연동 완료 |
| `E2` | `DONE` | no-docker CI 게이트(`env/docs/tests/procgraph/demo`) 고정 |
| `E3` | `DONE` | `demo_pack` 스키마/실패 분류 하드닝 완료 |
| `E4` | `DONE` | 정적 리포트 렌더러(`demo_report_view`) 추가 완료 |
| `E5` | `DONE` | scaffold 자동 export 등록 + opt-out 적용 완료 |
| `E6` | `DONE` | durable queue 경계/재시작 회귀 케이스 확장 완료 |

### 연구 트랙 상태 (`R-*`)

| 항목 | 상태 | 메모 |
|---|---|---|
| `R1` | `BLOCKED_BY_RESEARCH` | 의미론 결정이 연구 과제로 남아 있음 |
| `R2` | `BLOCKED_BY_RESEARCH` | ack ownership/dedup 정책 미확정 |
| `R3` | `BLOCKED_BY_RESEARCH` | runtime cycle 안전 모델 미확정 |
| `R4` | `BLOCKED_BY_RESEARCH` | 분산 오케스트레이션 모델 미확정 |
| `R5` | `BLOCKED_BY_RESEARCH` | cross-host payload lifecycle 미확정 |
| `R6` | `BLOCKED_BY_RESEARCH` | 보안/거버넌스 기준선 미확정 |

### 게이트 상태 (`G-*`)

| 게이트 | 상태 | 의존 |
|---|---|---|
| `G1` | `BLOCKED_BY_RESEARCH` | `R1` + `R2` |
| `G2` | `BLOCKED_BY_RESEARCH` | `R3` |
| `G3` | `BLOCKED_BY_RESEARCH` | `R4` |
| `G4` | `BLOCKED_BY_RESEARCH` | `R5` + `R6` |

## Agent 구현 트랙 (`E-*`)

### `E1` CI/환경 복구

- 목표: GitHub Actions green 상태와 로컬/CI 재현성(콘다 포함)을 고정한다.
- 산출물:
  - CI 워크플로우 보정 및 검증 명령 매트릭스 정리
  - 환경 이슈 대응 절차 문서
- 완료조건(DoD):
  - 동일 명령 세트가 로컬/CI에서 모두 통과
  - 실패 시 결정적인 메시지와 종료 코드 제공
- 검증 명령:
  - `python3 scripts/docs_hygiene.py --strict`
  - `python3 scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0`
  - `python scripts/demo_pack.py --profile ci`
- 리스크:
  - 로컬 conda 환경과 CI 이미지 간 의존성 드리프트

### `E2` 검증 게이트 강화

- 목표: 문서/테스트/그래프 검증을 PR 필수 게이트로 고정한다.
- 산출물:
  - strict docs hygiene + test hygiene + graph validate + demo profile 체인
  - 실패 분류 절차(운영 명령 문서 반영)
- 완료조건(DoD):
  - 머지 전 실패/성공 판정이 일관됨
  - 필수 체크의 무음 스킵이 없음
- 검증 명령:
  - `python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml`
  - `python scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml`
- 리스크:
  - optional dependency 누락으로 인한 오탐 실패

### `E3` 시연 품질 고정

- 목표: 코어 의미론 변경 없이 교수님 시연 출력의 가독성과 재현성을 높인다.
- 산출물:
  - `scripts/demo_pack.py` 요약/리포트 포맷 안정화
  - 실패 코드 가이드 명문화
- 완료조건(DoD):
  - S1/S2/S3 재현 절차가 단일 가이드에서 완결
  - 소스 코드를 열지 않고도 실패 진단 가능
- 검증 명령:
  - `python scripts/demo_pack.py --profile ci`
- 리스크:
  - 웹캠 경로의 하드웨어 편차

### `E4` 경량 시각화(연구 비의존)

- 목표: GUI 없이도 결과를 정적으로 확인할 수 있는 시각화 경로를 제공한다.
- 산출물:
  - JSON 리포트 -> Markdown/HTML 요약 변환 스크립트(또는 동등 기능)
  - CI 안전 사용법 문서
- 완료조건(DoD):
  - 하드웨어 없는 CI 프로필에서도 시각화 산출물 생성 가능
  - 시나리오 상태와 핵심 지표가 함께 출력됨
- 검증 명령:
  - `python scripts/demo_pack.py --profile ci`
  - 생성된 리포트 대상 시각화 명령
- 리스크:
  - 범위가 GUI 구현으로 확장될 가능성

### `E5` 플러그인 DX 마감

- 목표: source/node/sink 플러그인 작성 난이도를 낮춘다.
- 산출물:
  - scaffold 산출물 품질 개선
  - 템플릿 예시 및 가이드 정합성 보강
- 완료조건(DoD):
  - 생성된 source/node/sink 골격이 기본 테스트를 통과
  - 명령어 기준으로 재현 가능한 작성 흐름 확보
- 검증 명령:
  - scaffold 명령 + 생성 코드 기본 테스트
- 리스크:
  - 템플릿이 런타임 인터페이스와 어긋날 가능성

### `E6` 신뢰성 회귀 확장

- 목표: 단절/재시작/백로그 시나리오 회귀 검증을 강화한다.
- 산출물:
  - durable queue 경계조건 테스트 추가
  - replay/ack pass-fail 기준 명시
- 완료조건(DoD):
  - 주요 장애 계열 시나리오가 자동 테스트에 포함
  - 머지 전 회귀 탐지가 가능
- 검증 명령:
  - `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
- 리스크:
  - 제한된 CI 자원에서 플래키 테스트 발생

## 사용자 연구 트랙 (`R-*`)

### `R1` `N:N` 채널 의미론

- 연구질문: 다중 producer/consumer 채널에서 메시지 진행 소유권은 누구인가?
- 최소실험:
  - 1:2, 2:1, 2:2 조합에서 재처리/중복/지연 비교
- 성공판정:
  - 소유권과 순서 보장을 명시한 의미론 문서 확보
- 산출물:
  - 채널 의미론 결정서
- 차단 해제:
  - `G1`

### `R2` ACK ownership + dedup 정책

- 연구질문: ACK 주체와 dedup 키 범위(채널/프로세스/글로벌)는 어떻게 정할 것인가?
- 최소실험:
  - 키 충돌, 지연 ACK, 중복 전달 복구 케이스
- 성공판정:
  - 무손실/중복허용 경계를 포함한 정확성 계약 정리
- 산출물:
  - ACK/중복제거 계약 문서
- 차단 해제:
  - `G1`

### `R3` 순환 그래프 런타임 모델

- 연구질문: validator 허용 범위를 넘어 runtime loop를 어디까지 허용할 것인가?
- 최소실험:
  - delay/observer 기반 루프 안정성 및 정지조건 검증
- 성공판정:
  - 정지조건/폭주방지 포함 안전 규격 확정
- 산출물:
  - 순환 실행 안전장치 규격
- 차단 해제:
  - `G2`

### `R4` 프로세스 그래프 실행/오케스트레이션

- 연구질문: 단일 호스트 멀티 프로세스에서 분산까지 어떤 단계로 확장할 것인가?
- 최소실험:
  - local multi-proc 기준선 -> remote bridge 실험
- 성공판정:
  - 단계별 실행 모델과 실패복구 정책 수립
- 산출물:
  - 연구 트랙 실행모델 로드맵
- 차단 해제:
  - `G3`

### `R5` Cross-host `payload_ref` 전략

- 연구질문: URI/object-store ref의 수명주기와 권한 모델을 어떻게 설계할 것인가?
- 최소실험:
  - 로컬 file ref vs 네트워크/object-store ref 성능/복구 비교
- 성공판정:
  - 수명주기 규칙을 포함한 portability v2 초안 도출
- 산출물:
  - payload portability v2 제안서
- 차단 해제:
  - `G4`

### `R6` 보안/거버넌스 기준선

- 연구질문: 플러그인 실행 최소 신뢰정책(서명/시크릿/감사)은 어떻게 둘 것인가?
- 최소실험:
  - 악성 플러그인, 시크릿 오남용 시나리오 점검
- 성공판정:
  - 적용 가능한 최소 보안 기준 확정
- 산출물:
  - 보안/거버넌스 기준서
- 차단 해제:
  - `G4`

## 게이트 매트릭스 (`G-*`)

| 게이트 | 선행 연구 | 차단되는 구현 |
|---|---|---|
| `G1` | `R1` + `R2` 완료 전 | 런타임 `N:N` 채널 실행 |
| `G2` | `R3` 완료 전 | 런타임 순환 실행 허용 |
| `G3` | `R4` 완료 전 | 분산 오케스트레이터/컨트롤 플레인 구현 |
| `G4` | `R5` + `R6` 완료 전 | cross-host 바이너리 payload 기본 탑재 |

## 작업 계약(Working Contract)

### 보고 형식

- 모든 진행 보고는 다음을 포함한다:
  - step id (`P13.1`, SSOT 변경 전까지 고정)
  - 항목 id (`E*` 또는 `R*`)
  - 상태코드 (`READY`, `BLOCKED_BY_RESEARCH`, `DONE`)
  - 증거 경로(테스트 로그/문서 경로/CI 실행 기록)

### 상태코드 규칙

- `READY`: 연구 의사결정 없이 바로 실행 가능
- `BLOCKED_BY_RESEARCH`: 지정된 `R*` 산출물 전에는 구현 보류
- `DONE`: 증거 확보 + 매핑 문서 동기화까지 완료

### 동기화 규칙

- `E*` 범위가 바뀌면 같은 변경세트에서 함께 갱신:
  - `docs/roadmap/execution_roadmap.md`
  - `docs/progress/current_status.md`
  - `docs/reference/document_inventory.md`
- `R*`에서 결정이 확정되면 게이트 영향 반영:
  - `docs/roadmap/future_backlog.md`
  - 승격 시 `docs/roadmap/execution_roadmap.md`

### 가정/기본값

- 기준 상태는 `P12` 완료, in-proc 코어 런타임 유지.
- P13 실행 완결 사이클은 연구 제외 구현 항목(`E1`~`E6`) 완료 상태다.
- 날짜 고정보다 게이트 충족 순서를 우선한다.
- 연구 게이트 전에는 풀 GUI 대신 정적 시각화를 우선한다.
- 게이트에 막힌 구현은 선행 연구 산출물 승인 전 착수하지 않는다.
