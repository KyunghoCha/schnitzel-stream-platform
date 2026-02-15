# Execution Roadmap (Platform Pivot SSOT)

Last updated: 2026-02-15

Current step id: `P4.5`

## English

This document is the **execution SSOT** for the platform pivot.

Rule:
- When reporting progress (in issues/PRs/chat), always reference the **current step id** (example: `P1.4/8`).

### Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/contracts/stream_packet.md`, `PROMPT_CORE.md`.
- **Scope**: Track the ordered plan, status, and next actions for evolving `schnitzel-stream-platform` into a universal stream platform with a stable entrypoint.
- **Non-scope**: Final DAG semantics, distributed execution, and autopilot control plane (these are phased and provisional).

### Risks (P0–P3)

- **P0**: Plan drift: adding features without updating step status causes SSOT/code mismatch.
- **P1**: Over-design: locking DAG/type systems too early can block shipping.
- **P2**: Under-design: shipping runtime without validation/backpressure risks instability on edge.
- **P3**: Doc fragmentation: multiple “plans” competing as SSOT.

### Mismatches (path)

- Legacy CCTV-only roadmap is preserved at `docs/roadmap/legacy_cctv_execution_roadmap_2026-02-08.md` (historical reference, not SSOT).

### Fix Plan

Status legend:
- `DONE`: completed and merged on `main`
- `NOW`: next work to execute
- `NEXT`: queued after NOW
- `LATER`: not started

#### Phase 0: Entrypoint SSOT + Strangler (DONE ~100%)

- `P0.1` Cross-platform LF canonical (`.gitattributes`). `DONE` (291874c)
- `P0.2` Introduce `schnitzel_stream` core skeleton. `DONE` (287abde)
- `P0.3` Phase 0 job spec + legacy job runner. `DONE` (29cb3ed)
- `P0.4` New CLI entrypoint `python -m schnitzel_stream`. `DONE` (5cd6c43)
- `P0.5` Migrate tests/scripts/Docker/docs, disable legacy CLI. `DONE` (c729fb9, 62786b7, aa8d515)
- `P0.6` SSOT docs for pivot (architecture/plan/support matrix/roadmap refinement). `DONE` (5e30823, 151676c, 4f1ab87, 92567af)
- `P0.7` StreamPacket contract SSOT + references. `DONE` (f34f876)

Current position: **Phase 4** (legacy decommission is now the priority; `P3.3` is deferred)

#### Phase 1: Graph Runtime MVP (strict DAG) + StreamPacket Adoption (DONE ~100%)

- `P1.1` Draft graph model + strict DAG validator + unit tests. `DONE` (27bb702)
- `P1.2` Draft node-graph spec v2 loader + unit tests. `DONE` (2822ffa, 87d7a24)
- `P1.3` Centralize plugin allowlist checks in `PluginPolicy`. `DONE` (4d95fd5)
- `P1.4` CLI: add `validate` / `--validate-only` to validate v1(job) and v2(node graph). `DONE` (f4322d4)
- `P1.5` Runtime MVP: execute v2 graph (topological order) for in-proc packets only. `DONE` (7e1a9e7)
- `P1.6` Type/port/transport-compat validation (static). `DONE` (3fe090a)
- `P1.7` Restricted cycles policy (Delay/InitialValue only) as a validator extension. `DONE` (53b38a9)

#### Phase 2: Durable Delivery Hardening (DONE ~100%)

- `P2.1` Durable queue node plugin (`WAL/SQLite`), store-and-forward. `DONE` (fd02823)
- `P2.2` Idempotency keys and ack semantics. `DONE` (e885e41)
- `P2.3` Soak tests for outage/restart/backlog replay. `DONE` (9dabf8d)

#### Phase 3: Control Plane (IN PROGRESS ~60–75%)

- `P3.1` Unified metrics/health contract across transports. `DONE` (e6d14c5)
- `P3.2` Autonomic tuning hooks (policy-driven throttles). `DONE` (a792677)
- `P3.3` Optional LLM/controller layer (human-in-the-loop, gated). `NEXT` (optional)

#### Phase 4: Legacy Decommission (IN PROGRESS)

Intent:
- Remove `legacy/ai/*` only after v2 graphs cover the required production behavior.
- Prefer extraction (separate package/repo) over hard-delete if external users still depend on it.
- Legacy removal requires a **deprecation window**: do not delete `legacy/ai/*` earlier than **90 days after** `P4.3` lands.

- `P4.1` Define v2 parity scope + cutover criteria (what “legacy can be removed” means). `DONE` (ba2cb85) (SSOT: `docs/roadmap/legacy_decommission.md`)
- `P4.2` Implement v2 CCTV pipeline graph + nodes to reach parity (source/model/policy/sink). `DONE` (P4.2.1-P4.2.5)
  - `P4.2.1` Port critical policy nodes (zones/dedup) into `schnitzel_stream` + tests + demo graph. `DONE` (ba6ea9d, 2ef7481, 1b0aa83, d14abcf)
  - `P4.2.2` v2 event builder (protocol v0.2) node + tests. `DONE` (8860377, 618b20a, 8f558b2)
  - `P4.2.3` v2 file-video source + sampler nodes + tests. `DONE` (a2e34fa, 6d8cd5e, 570409f)
  - `P4.2.4` v2 mock model/detection node (frame -> detection) + tests. `DONE` (6af347c, 201f808)
  - `P4.2.5` v2 end-to-end CCTV demo graph + golden/regression test. `DONE` (4b8408b, cb20638)
- `P4.3` Switch default graph to v2 and start a deprecation window for v1 legacy job. `DONE` (248b10d, 9aa7a4d, 0ff8387, bd818f5)
- `P4.4` Extract legacy runtime (`legacy/ai/*`) to a separate package/repo or move under `legacy/` with pinned deps. `DONE` (cefd89f, 37d7537, a57ee5a)
- `P4.5` Remove legacy runtime from main tree after the deprecation window. `NEXT` (>= 90 days after `P4.3`)

### Verification

- Executed (local): `python3 -m compileall -q src tests`
- Not executed (local): `pytest` (depends on venv deps; CI should enforce on push)

### Open Questions

- What is the Phase 1 runtime execution model?
  - push vs pull, batching/windowing, and backpressure semantics
- What is the minimal port/type system to prevent invalid graphs without overfitting to CCTV?
- What is the official edge support matrix (OS/arch/GPU) and packaging lane policy (Docker required or optional)?

---

## 한국어

이 문서는 플랫폼 피벗을 위한 **실행 SSOT** 입니다.

규칙:
- 진행 상황을 보고(이슈/PR/채팅)할 때 항상 **current step id** 를 함께 언급합니다. (예: `P1.4/8`)

### 요약

- **참조 SSOT 문서**: `docs/roadmap/strategic_roadmap.md`, `docs/contracts/stream_packet.md`, `PROMPT_CORE.md`.
- **범위**: `schnitzel-stream-platform`을 안정적인 엔트리포인트를 가진 범용 스트림 플랫폼으로 진화시키기 위한 순서/상태/다음 액션을 추적합니다.
- **비범위**: 최종 DAG 의미론, 분산 실행, 오토파일럿 컨트롤 플레인(각각 단계적으로 정의되며 잠정입니다).

### 리스크 (P0–P3)

- **P0**: 계획 드리프트: SSOT에 step 상태를 업데이트하지 않은 채 기능을 추가하면 SSOT/코드 불일치가 발생합니다.
- **P1**: 과설계: DAG/타입 시스템을 너무 빨리 고정하면 출시를 막을 수 있습니다.
- **P2**: 과소설계: 검증/백프레셔 없이 런타임을 배포하면 엣지에서 불안정성이 커집니다.
- **P3**: 문서 파편화: 여러 “계획” 문서가 SSOT처럼 경쟁하면 실행이 깨집니다.

### 불일치(경로)

- 레거시 CCTV 전용 로드맵은 `docs/roadmap/legacy_cctv_execution_roadmap_2026-02-08.md` 에 보존합니다. (역사 기록용, SSOT 아님)

### 실행 계획

상태 표기:
- `DONE`: 완료되어 `main`에 머지됨
- `NOW`: 지금 실행할 작업
- `NEXT`: NOW 이후 대기
- `LATER`: 아직 시작하지 않음

#### Phase 0: Entrypoint SSOT + Strangler (DONE ~100%)

- `P0.1` Cross-platform LF canonical (`.gitattributes`). `DONE` (291874c)
- `P0.2` Introduce `schnitzel_stream` core skeleton. `DONE` (287abde)
- `P0.3` Phase 0 job spec + legacy job runner. `DONE` (29cb3ed)
- `P0.4` New CLI entrypoint `python -m schnitzel_stream`. `DONE` (5cd6c43)
- `P0.5` Migrate tests/scripts/Docker/docs, disable legacy CLI. `DONE` (c729fb9, 62786b7, aa8d515)
- `P0.6` SSOT docs for pivot (architecture/plan/support matrix/roadmap refinement). `DONE` (5e30823, 151676c, 4f1ab87, 92567af)
- `P0.7` StreamPacket contract SSOT + references. `DONE` (f34f876)

현재 위치: **Phase 4** (legacy decommission이 우선순위이며, `P3.3`는 보류됨)

#### Phase 1: Graph Runtime MVP (strict DAG) + StreamPacket Adoption (DONE ~100%)

- `P1.1` Draft graph model + strict DAG validator + unit tests. `DONE` (27bb702)
- `P1.2` Draft node-graph spec v2 loader + unit tests. `DONE` (2822ffa, 87d7a24)
- `P1.3` Centralize plugin allowlist checks in `PluginPolicy`. `DONE` (4d95fd5)
- `P1.4` CLI: add `validate` / `--validate-only` to validate v1(job) and v2(node graph). `DONE` (f4322d4)
- `P1.5` Runtime MVP: execute v2 graph (topological order) for in-proc packets only. `DONE` (7e1a9e7)
- `P1.6` Type/port/transport-compat validation (static). `DONE` (3fe090a)
- `P1.7` Restricted cycles policy (Delay/InitialValue only) as a validator extension. `DONE` (53b38a9)

#### Phase 2: Durable Delivery Hardening (DONE ~100%)

- `P2.1` Durable queue node plugin (`WAL/SQLite`), store-and-forward. `DONE` (fd02823)
- `P2.2` Idempotency keys and ack semantics. `DONE` (e885e41)
- `P2.3` Soak tests for outage/restart/backlog replay. `DONE` (9dabf8d)

#### Phase 3: Control Plane (IN PROGRESS ~60–75%)

- `P3.1` Unified metrics/health contract across transports. `DONE` (e6d14c5)
- `P3.2` Autonomic tuning hooks (policy-driven throttles). `DONE` (a792677)
- `P3.3` Optional LLM/controller layer (human-in-the-loop, gated). `NEXT` (optional)

#### Phase 4: Legacy Decommission (IN PROGRESS)

의도(Intent):
- v2 그래프가 필요한 운영 동작을 커버한 이후에만 `legacy/ai/*`를 제거합니다.
- 외부 사용자가 여전히 의존한다면 hard-delete 대신 추출(별도 패키지/리포) 우선입니다.
- 레거시 제거는 **deprecation window**가 필요합니다: `P4.3` 머지 이후 **최소 90일** 이전에 `legacy/ai/*`를 삭제하지 않습니다.

- `P4.1` Define v2 parity scope + cutover criteria (what “legacy can be removed” means). `DONE` (ba2cb85) (SSOT: `docs/roadmap/legacy_decommission.md`)
- `P4.2` Implement v2 CCTV pipeline graph + nodes to reach parity (source/model/policy/sink). `DONE` (P4.2.1-P4.2.5)
  - `P4.2.1` Port critical policy nodes (zones/dedup) into `schnitzel_stream` + tests + demo graph. `DONE` (ba6ea9d, 2ef7481, 1b0aa83, d14abcf)
  - `P4.2.2` v2 event builder (protocol v0.2) node + tests. `DONE` (8860377, 618b20a, 8f558b2)
  - `P4.2.3` v2 file-video source + sampler nodes + tests. `DONE` (a2e34fa, 6d8cd5e, 570409f)
  - `P4.2.4` v2 mock model/detection node (frame -> detection) + tests. `DONE` (6af347c, 201f808)
  - `P4.2.5` v2 end-to-end CCTV demo graph + golden/regression test. `DONE` (4b8408b, cb20638)
- `P4.3` Switch default graph to v2 and start a deprecation window for v1 legacy job. `DONE` (248b10d, 9aa7a4d, 0ff8387, bd818f5)
- `P4.4` Extract legacy runtime (`legacy/ai/*`) to a separate package/repo or move under `legacy/` with pinned deps. `DONE` (cefd89f, 37d7537, a57ee5a)
- `P4.5` Remove legacy runtime from main tree after the deprecation window. `NEXT` (>= 90 days after `P4.3`)

### 검증

- 실행됨(로컬): `python3 -m compileall -q src tests`
- 실행 안 함(로컬): `pytest` (venv deps 필요; push 시 CI가 강제)

### 미해결 질문

- Phase 1 런타임 실행 모델은 무엇인가?
  - push vs pull, 배치/윈도우, 백프레셔 의미론
- CCTV에 과적합하지 않으면서도 invalid graph를 막는 최소 port/type 시스템은 무엇인가?
- 공식 엣지 지원 매트릭스(OS/arch/GPU)와 패키징 레인 정책은 무엇인가? (Docker 필수 vs 옵션)
