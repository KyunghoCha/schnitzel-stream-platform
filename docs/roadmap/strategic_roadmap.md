# Strategic Roadmap: schnitzel-stream-platform

Last updated: 2026-02-15

## English

## Purpose

This document defines long-term direction for `schnitzel-stream-platform`.
It does **not** track execution status or completion percentages.

Roadmap stack:
- Execution status SSOT: `docs/roadmap/execution_roadmap.md`
- Candidate backlog: `docs/roadmap/future_backlog.md`
- Historical/completed sub-plans: `legacy/docs/archive/roadmap_legacy/`

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

## 목적

이 문서는 `schnitzel-stream-platform`의 장기 방향을 정의한다.
이 문서에서는 실행 상태나 완료율을 추적하지 않는다.

로드맵 스택:
- 실행 상태 SSOT: `docs/roadmap/execution_roadmap.md`
- 후보 백로그: `docs/roadmap/future_backlog.md`
- 완료/역사 하위 계획: `legacy/docs/archive/roadmap_legacy/`

## North Star

다음 성질을 갖는 범용 스트림 플랫폼을 목표로 한다.
- 계약 우선(`StreamPacket`)
- 플러그인 우선(source/transform/compute/policy/sink)
- 엣지 안전성(복구/백프레셔/재전송)
- 크로스 플랫폼(Linux/Windows/macOS)
- 마이그레이션 친화(레거시는 Active SSOT가 아닌 아카이브로 보존)

## 전략 축

1. Contract Integrity
- packet/observability 계약을 안정적으로 명시한다.
- 그래프 토폴로지/전송 호환성 오류는 실행 전에 fail-closed 처리한다.

2. Runtime Reliability
- 부하 상황에서도 스트리밍 의미론을 결정적으로 유지한다.
- 실패 정책(retry/idempotency/backpressure/drop)을 명시한다.

3. Plugin Boundary Discipline
- 도메인 로직은 가능하면 코어 런타임 밖(플러그인 경계)으로 둔다.
- 전송/페이로드 이식성 규칙은 실행 전에 validator로 강제한다.

4. Cross-Platform Operations
- no-Docker/Docker 실행 레인을 명확히 유지한다.
- 엣지 운영 규약(경로/로그/서비스 모드)을 문서화한다.

5. Documentation Governance
- active vs legacy 경계를 강제한다.
- 실행 SSOT는 하나만 유지하고, 완료된 하위 계획은 아카이브로 이동한다.

## 연구 방향 (실행 확정 아님)

R1. validator-only 제약을 넘어서는 cycle-capable 그래프 런타임.

R2. 멀티 노드 오케스트레이션/분산 스케줄링 모델.

R3. 사람 개입형 컨트롤러 레이어(LLM 보조 포함).

위 항목은 전략 방향이며, 일정/단계 관리는 실행 로드맵에서만 다룬다.

## 본 문서 비범위

- phase별 완료율
- step 단위 실행 상태
- 커밋 단위 진행 로그

## 업데이트 규칙

전략이 바뀔 때만 이 문서를 갱신한다.
운영 진행 상태 업데이트는 `docs/roadmap/execution_roadmap.md`에서만 수행한다.
