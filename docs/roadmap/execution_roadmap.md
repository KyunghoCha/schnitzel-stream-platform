# Execution Roadmap (Platform Pivot SSOT)

Last updated: 2026-02-16

Current step id: `P3.3`

## English

This document is the **execution SSOT** for the platform pivot.

Rule:
- When reporting progress (in issues/PRs/chat), always reference the **current step id** (example: `P1.4/8`).

### Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/contracts/stream_packet.md`, `PROMPT_CORE.md`.
- **Scope**: Track the ordered plan, status, and next actions for evolving `schnitzel-stream-platform` into a universal stream platform with a stable entrypoint.
- **Non-scope**: Final DAG semantics, distributed execution, and autopilot control plane (these are phased and provisional).

### Roadmap Roles

- `docs/roadmap/execution_roadmap.md`: execution status and step ownership (this file)
- `docs/roadmap/strategic_roadmap.md`: long-term direction/principles (no step-by-step status tracking)
- `docs/roadmap/future_backlog.md`: candidate items with no committed schedule
- completed/historical sub-plans: git history/tag `pre-legacy-purge-20260216` (reference only)

### Risks (P0–P3)

- **P0**: Plan drift: adding features without updating step status causes SSOT/code mismatch.
- **P1**: Over-design: locking DAG/type systems too early can block shipping.
- **P2**: Under-design: shipping runtime without validation/backpressure risks instability on edge.
- **P3**: Doc fragmentation: multiple “plans” competing as SSOT.

### Mismatches (path)

- Legacy CCTV-only roadmap is preserved in git history/tag `pre-legacy-purge-20260216` (historical reference, not SSOT).

### Fix Plan

Status legend:
- `DONE`: completed and merged on `main`
- `NOW`: next work to execute
- `NEXT`: queued after NOW
- `LATER`: not started
- `GATED`: blocked by an explicit precondition (ex: deprecation window)

#### Phase 0: Entrypoint SSOT + Strangler (DONE ~100%)

- `P0.1` Cross-platform LF canonical (`.gitattributes`). `DONE` (291874c)
- `P0.2` Introduce `schnitzel_stream` core skeleton. `DONE` (287abde)
- `P0.3` Phase 0 job spec + legacy job runner. `DONE` (29cb3ed)
- `P0.4` New CLI entrypoint `python -m schnitzel_stream`. `DONE` (5cd6c43)
- `P0.5` Migrate tests/scripts/Docker/docs, disable legacy CLI. `DONE` (c729fb9, 62786b7, aa8d515)
- `P0.6` SSOT docs for pivot (architecture/plan/support matrix/roadmap refinement). `DONE` (5e30823, 151676c, 4f1ab87, 92567af)
- `P0.7` StreamPacket contract SSOT + references. `DONE` (f34f876)

Current position: **Phase 11 demo packaging complete** (`P3.3` remains optional research track)

#### Phase 1: Graph Runtime MVP (strict DAG) + StreamPacket Adoption (DONE ~100%)

- `P1.1` Draft graph model + strict DAG validator + unit tests. `DONE` (27bb702)
- `P1.2` Draft node-graph spec v2 loader + unit tests. `DONE` (2822ffa, 87d7a24)
- `P1.3` Centralize plugin allowlist checks in `PluginPolicy`. `DONE` (4d95fd5)
- `P1.4` CLI: add `validate` / `--validate-only` for graph validation (v2 node graph baseline). `DONE` (f4322d4)
- `P1.5` Runtime MVP: execute v2 graph (topological order) for in-proc packets only. `DONE` (7e1a9e7)
- `P1.6` Type/port/transport-compat validation (static). `DONE` (3fe090a)
- `P1.7` Restricted cycles policy (Delay/InitialValue only) as a validator extension. `DONE` (53b38a9)

#### Phase 2: Durable Delivery Hardening (DONE ~100%)

- `P2.1` Durable queue node plugin (`WAL/SQLite`), store-and-forward. `DONE` (fd02823)
- `P2.2` Idempotency keys and ack semantics. `DONE` (e885e41)
- `P2.3` Soak tests for outage/restart/backlog replay. `DONE` (9dabf8d)

#### Phase 3: Ops Control Surface (DONE core; research optional)

Intent:
- Phase 3 is **not** a multi-camera orchestrator or a distributed scheduler.
- Phase 3 is the minimal "control surface" required to run safely on edge: metrics/health contracts and policy-driven tuning hooks.

- `P3.1` Unified metrics/health contract across transports. `DONE` (e6d14c5)
- `P3.2` Autonomic tuning hooks (policy-driven throttles). `DONE` (a792677)
- `P3.3` Optional LLM/controller layer (human-in-the-loop, gated). `NEXT` (optional)

#### Phase 4: Legacy Decommission (DONE)

Intent:
- Legacy runtime removal was executed after v2 graph coverage was validated.
- Prefer extraction (separate package/repo) over hard-delete if external users still depend on it.
- Legacy removal default used a **deprecation window** policy tied to `P4.3`.
- Owner override path required explicit approval + checklist evidence (historical record in git history/tag).

- `P4.1` Define v2 parity scope + cutover criteria (what “legacy can be removed” means). `DONE` (ba2cb85) (historical record in git history/tag)
- `P4.2` Implement v2 CCTV pipeline graph + nodes to reach parity (source/model/policy/sink). `DONE` (P4.2.1-P4.2.5)
  - `P4.2.1` Port critical policy nodes (zones/dedup) into `schnitzel_stream` + tests + demo graph. `DONE` (ba6ea9d, 2ef7481, 1b0aa83, d14abcf)
  - `P4.2.2` v2 event builder (protocol v0.2) node + tests. `DONE` (8860377, 618b20a, 8f558b2)
  - `P4.2.3` v2 file-video source + sampler nodes + tests. `DONE` (a2e34fa, 6d8cd5e, 570409f)
  - `P4.2.4` v2 mock model/detection node (frame -> detection) + tests. `DONE` (6af347c, 201f808)
  - `P4.2.5` v2 end-to-end CCTV demo graph + golden/regression test. `DONE` (4b8408b, cb20638)
- `P4.3` Switch default graph to v2 and start a deprecation window for v1 legacy job. `DONE` (248b10d, 9aa7a4d, 0ff8387, bd818f5)
- `P4.4` Extract/quarantine legacy runtime with pinned dependencies before final removal. `DONE` (cefd89f, 37d7537, a57ee5a)
- `P4.5` Remove legacy runtime from main tree after deprecation window or approved owner override. `DONE` (owner override executed; legacy runtime removed on `main`)

#### Phase 5: Platform Generalization (Domain-Neutral) (DONE)

Intent:
- Phase 5 makes the repo feel like a **universal stream platform**, not a CCTV project:
  - domain-specific things remain supported, but they live behind plugin boundaries
  - docs/examples naming should be domain-neutral by default

- `P5.1` Docs + examples taxonomy cleanup (platform vs legacy) and naming de-CCTVization. `DONE` (48455a1, 41e9439, f389234)
  - DoD:
    - Top-level entry docs (`README.md`, `PROMPT*.md`, `docs/index.md`) clearly separate `platform` vs `legacy`.
    - Legacy-only docs/specs are removed from active docs and preserved in git history/tag.
    - Default/example v2 graphs avoid CCTV-specific naming unless the example is explicitly legacy.
- `P5.2` Plugin boundary hardening for IO (sources/sinks) and policy nodes. `DONE` (05719be, 5925f2e)
  - DoD:
    - RTSP/webcam/file sources are "just" `source` plugins (no core coupling).
    - backend/JSONL/stdout are "just" `sink` plugins.
    - `schnitzel_stream` core remains free of CCTV/backend schema assumptions (contract stays `StreamPacket`).

#### Phase 6: Streaming In-Proc Runtime Semantics (DONE)

Problem:
- The current in-proc runner executes each source to completion before downstream nodes run. That is OK for tiny demos but not OK for streaming sources (RTSP/webcam) or large files.

Intent:
- Evolve the runtime from a "batch DAG evaluator" into a "streaming packet scheduler" while keeping strict DAG safety by default.

- `P6.1` Interleaved scheduler: process packets incrementally (no unbounded buffering before downstream). `DONE` (282a74a)
  - DoD:
    - Sources can be infinite iterators without starving downstream nodes.
    - Downstream processing happens as packets flow (bounded queues).
    - Deterministic stop conditions exist (`--max-packets` / time budget / throttle policy).
- `P6.2` Backpressure + queue policy: bounded inbox, drop/slowdown semantics, and metrics. `DONE` (8e1b5db)
  - DoD:
    - configurable per-node inbox limits
    - metrics reflect drops/backpressure events

#### Phase 7: Payload Portability + Transport Lanes (DONE)

Intent:
- Make "what can cross a boundary" explicit (in-proc objects vs durable/IPC/network portability).

- `P7.1` Payload portability policy + validator enforcement. `DONE` (18ddb75)
  - DoD:
    - graphs fail validation if a non-portable payload (ex: raw frames) is routed through durable/network lanes
    - durable queue nodes are explicitly documented as JSON-only until a blob/handle strategy exists
- `P7.2` Blob/handle strategy (`payload_ref`) for large/binary payloads (frames, audio). `DONE` (c4d40bf)
  - DoD:
    - `StreamPacket` supports a portable reference form (file/shm/uri) with clear lifecycle rules

#### Phase 8: IO Plugin Packs (RTSP/Webcam/HTTP/etc) (DONE)

Intent:
- Treat RTSP and "backend" as replaceable adapters. Platform ships with minimal batteries; deployments can bring their own.

- `P8.1` RTSP source plugin (reconnect/backoff) + tests + demo graph. `DONE` (8cf52e8, 471ff6c)
- `P8.2` Webcam source plugin + tests + demo graph. `DONE` (3d9e889, 9886e63)
- `P8.3` HTTP sink plugin (idempotency + retry policy) + tests + demo graph. `DONE` (2d7442c, 83baaad)
- `P8.4` JSONL/file sink plugin + tests. `DONE` (983be3f, c9f831e)

#### Phase 9: Cross-Platform Packaging + Release Discipline (DONE)

- `P9.1` Finalize support matrix and packaging lanes (Docker + no-Docker). `DONE` (36a588c, 166b95e)
  - DoD:
    - documented target list (OS/arch) and lane policy
    - CI verifies at least one "no-Docker" lane (`pip` + venv) end-to-end
    - optional: multi-arch Docker build lane
- `P9.2` Edge ops conventions (paths, service mode, logs) hardened. `DONE` (880be80)

#### Phase 10: Hardening & DX (DONE)

Intent:
- Lock quality/documentation gates so platform changes do not drift.
- Remove legacy CLI compatibility shims and keep only v2 graph-native interfaces.
- Lower plugin authoring cost with scaffolding and explicit profile contracts.

- `P10.1` SSOT realignment for hardening track (step id switch, docs sync). `DONE` (e73925a)
- `P10.2` Quality gate hardening (docs hygiene + broken reference checks in CI). `DONE` (965deb4)
- `P10.3` Remove legacy CLI compatibility flags and migrate helper scripts to graph-native flow. `DONE` (1fec4c2, e574ee1)
- `P10.4` Plugin scaffold SDK (code/test/graph templates + guide). `DONE` (b7de1b2)
- `P10.5` Payload profile v1 (`inproc_any`/`json_portable`/`ref_portable`) with validator bridge. `DONE` (5f1e66a)

#### Phase 11: Demo Packaging & Reproducibility (DONE)

Intent:
- Ship a reproducible professor showcase package without changing runtime core semantics.
- Keep this cycle product-focused: demo reliability, command ergonomics, and documentation clarity.
- Keep distributed/governance/control-plane work out of this execution track.

- `P11.1` SSOT switch to demo track + scope freeze. `DONE` (2799e5e)
- `P11.2` Freeze 3 showcase scenarios (in-proc, durable replay, webcam). `DONE` (16b451f)
- `P11.3` Add one-command demo runner (`scripts/demo_pack.py`) with profile-based flow + report. `DONE` (16b451f)
- `P11.4` Add manual showcase guide and command docs expansion. `DONE` (b7712b3)
- `P11.5` Add demo-pack tests + CI smoke integration (`--profile ci`). `DONE` (032752d, 1f76708)
- `P11.6` Sync docs mapping/inventory/status for showcase assets. `DONE`

#### Research Track (Not On Critical Path)

Intent:
- Orchestrators/LLM controllers can be thesis-grade work; keep them out of the critical path until the core platform is stable.

- `R1` Cycle-capable runtime semantics (beyond validator-only) with safety guardrails. `LATER`
- `R2` Multi-camera orchestrator/process manager/inference server architecture. `LATER`
- `R3` LLM/controller layer (human-in-the-loop). `LATER`

### Verification

- Executed (local): `python3 -m compileall -q src tests`
- Not executed (local): `pytest` (depends on venv deps; CI should enforce on push)

### Open Questions

- What is the Phase 1 runtime execution model?
  - push vs pull, batching/windowing, and backpressure semantics
- What is the minimal port/type system to prevent invalid graphs without overfitting to CCTV?
- What is the communication plan for external users that still reference historical `ai.*` docs/examples?

---

## 한국어

이 문서는 플랫폼 전환 작업의 **실행 상태 SSOT**다.
세부 설계 원칙은 전략 문서에서, 아이디어 후보는 백로그 문서에서 관리한다.

운영 규칙:
- 진행 보고(이슈/PR/채팅)에는 반드시 현재 step id를 함께 적는다.
- 상태/우선순위 변경은 이 문서를 먼저 갱신한 뒤 코드 변경을 진행한다.

### 문서 역할

- 실행 상태: `docs/roadmap/execution_roadmap.md` (본 문서)
- 장기 방향: `docs/roadmap/strategic_roadmap.md`
- 후보 과제: `docs/roadmap/future_backlog.md`
- 완료/역사 계획: git 이력/태그 `pre-legacy-purge-20260216`

### 현재 상태 한눈에 보기

- current step id: `P3.3`
- 전체 위치: **P0~P11 핵심 항목 완료, P3.3은 선택 연구 트랙으로 유지**
- 레거시 런타임(관련 레거시 경로)은 `main`에서 제거 완료

상태 표기:
- `DONE`: 완료되어 `main` 반영
- `NEXT`: 다음 후보
- `LATER`: 연구/후순위

### 단계 요약

| 구간 | 상태 | 메모 |
|---|---|---|
| Phase 0 | DONE | 엔트리포인트 통합, 기본 SSOT 정착 |
| Phase 1 | DONE | v2 그래프 로더/검증기/실행기 기본선 확립 |
| Phase 2 | DONE | durable queue, 재전송/멱등성 기반 강화 |
| Phase 3 | DONE (core), NEXT (P3.3) | 운영 제어면(메트릭/스로틀) 완료, LLM 컨트롤러는 선택 과제 |
| Phase 4 | DONE | v2 전환 완료 및 레거시 런타임 제거 |
| Phase 5 | DONE | 도메인 중립 네이밍/경계 정리 |
| Phase 6 | DONE | 스트리밍 in-proc 스케줄링/백프레셔 정착 |
| Phase 7 | DONE | payload 이식성 규칙 + `payload_ref` 전략 반영 |
| Phase 8 | DONE | RTSP/Webcam/HTTP/JSONL 등 IO 플러그인 팩 정리 |
| Phase 9 | DONE | 패키징/릴리즈 규율 및 엣지 운영 규약 정리 |
| Phase 10 | DONE | 품질 게이트/CLI 정리/플러그인 DX/데이터 프로파일 하드닝 |
| Phase 11 | DONE | 교수님 시연용 데모 패키지/재현성 고정 |

### 현재 우선순위

1. `P3.3` (optional): 사람 승인 기반 컨트롤러 계층 범위 검토
2. 연구 트랙(`R1~R3`)은 제품 트랙과 분리 유지
3. 데모 패키지(`showcase_*`, `scripts/demo_pack.py`)의 운영 피드백 기반 개선

### 레거시 관련 기준

- 레거시 제거 계획/체크리스트는 워킹 트리에서 제거되었으며 git 이력/태그로 관리한다.
- 참조: `pre-legacy-purge-20260216`

### 검증 상태

- 로컬 실행 완료: `python3 -m compileall -q src tests`
- 로컬 미실행: `pytest` (개발 의존성 설치 필요, push 시 CI 검증 권장)

### 열린 쟁점

1. 순환 그래프 실행 모델을 어디까지 런타임에 편입할지(`R1`)
2. 분산 실행 시 전송/스케줄링 책임 경계를 어떻게 나눌지(`R2`)
3. `P3.3`/연구 트랙(`R1~R3`) 재개 시점을 어떤 운영 신호로 판단할지
