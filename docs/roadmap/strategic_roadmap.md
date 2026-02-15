# Strategic Roadmap: schnitzel-stream-platform

Last updated: 2026-02-16

## English

## Purpose

This document defines long-term direction for `schnitzel-stream-platform`.
It does **not** track execution status or completion percentages.

Roadmap stack:
- Execution status SSOT: `docs/roadmap/execution_roadmap.md`
- Candidate backlog: `docs/roadmap/future_backlog.md`
- Historical/completed sub-plans: git history/tag `pre-legacy-purge-20260216`

## North Star

Build a universal stream platform that is:
- contract-first (`StreamPacket`)
- plugin-first (source/transform/compute/policy/sink)
- edge-safe (resilience/backpressure/replay)
- cross-platform (Linux/Windows/macOS)
- migration-friendly (legacy preserved as archive, not active SSOT)

## Strategic Pillars

1. Contract Integrity
- Keep packet/observability contracts stable and explicit.
- Fail closed on invalid graph topology or transport compatibility.

2. Runtime Reliability
- Keep streaming semantics deterministic under load.
- Make failure policy explicit (retry/idempotency/backpressure/drop semantics).

3. Plugin Boundary Discipline
- Keep domain logic outside core runtime whenever possible.
- Ensure transport and payload portability rules are validated before runtime.

4. Cross-Platform Operations
- Maintain clear no-Docker and Docker execution lanes.
- Keep edge operation conventions (path, logging, service mode) documented.

5. Documentation Governance
- Enforce active vs legacy boundaries.
- Keep one execution SSOT and archive completed sub-plans.

## Research Directions (Not Execution Commitments)

R1. Cycle-capable graph runtime beyond validator-only constraints.

R2. Multi-node orchestration and distributed scheduling model.

R3. Human-in-the-loop controller layer (including LLM-assisted controls).

These are strategic directions only. Scheduling belongs to the execution roadmap.

## Out of Scope for This Document

- Per-phase completion percentages
- Step-by-step task status
- Commit-level progress logs

## Update Rule

Update this document only when strategy changes.
For operational progress updates, modify `docs/roadmap/execution_roadmap.md` instead.

---

## 한국어

## 문서 성격

이 문서는 `schnitzel-stream-platform`의 **장기 방향**을 정리하는 전략 문서다.
진행률, 단계별 상태, 커밋 내역은 이 문서에서 관리하지 않는다.

로드맵 체계:
- 실행 상태 SSOT: `docs/roadmap/execution_roadmap.md`
- 후보 과제 백로그: `docs/roadmap/future_backlog.md`
- 완료된 과거 계획 아카이브: git 이력/태그 `pre-legacy-purge-20260216`

## 지향점

플랫폼은 아래 성질을 동시에 만족해야 한다.
- 계약 중심: 데이터 계약(`StreamPacket`)이 흔들리지 않아야 함
- 플러그인 중심: source/transform/compute/policy/sink 경계를 분명히 유지
- 엣지 안정성: 장애 복구, 백프레셔, 재전송 규칙을 기본 내장
- 크로스 플랫폼: Linux/Windows/macOS 실행 경로를 지속 보장
- 마이그레이션 친화: 레거시는 운영 경로가 아니라 기록 보관 경로로 관리

## 핵심 원칙

1. 계약 일관성
- packet/observability 계약은 명시적으로 문서화하고 보수적으로 변경한다.
- 그래프/전송 호환성 오류는 실행 전에 차단한다.

2. 런타임 신뢰성
- 부하가 걸려도 스트리밍 의미론이 예측 가능해야 한다.
- 재시도, 멱등성, 드롭 정책 등 실패 동작을 숨기지 않고 드러낸다.

3. 플러그인 경계 규율
- 도메인별 처리 로직은 가능한 한 코어에서 분리한다.
- 페이로드 이식성/전송 제약은 validator로 사전 강제한다.

4. 운영 일관성
- Docker/no-Docker 실행 레인을 둘 다 유지한다.
- 엣지 운영 규약(경로, 로그, 서비스 모드)을 문서 기준으로 통일한다.

5. 문서 거버넌스
- active 문서와 legacy 문서의 경계를 유지한다.
- 실행 상태 문서는 하나만 SSOT로 유지하고, 종료된 계획은 즉시 아카이브한다.

## 연구 방향 (일정 미확정)

- R1: validator 제약을 넘는 순환 그래프 실행 모델
- R2: 멀티 노드 오케스트레이션과 분산 스케줄링
- R3: 사람 승인 기반 컨트롤러 계층(LLM 보조 포함)

위 항목은 “해야 할 일 목록”이 아니라 “방향성”이다.
실행 일정과 단계는 `docs/roadmap/execution_roadmap.md`에서만 확정한다.

## 비범위

- 단계별 완료율
- step 단위 진행 상태
- 커밋 단위 작업 로그

## 갱신 규칙

전략이 바뀔 때만 이 문서를 갱신한다.
운영 진행 업데이트는 `docs/roadmap/execution_roadmap.md`에서 처리한다.
