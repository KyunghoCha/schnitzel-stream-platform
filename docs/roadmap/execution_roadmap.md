# Execution Roadmap (Platform Pivot SSOT)

Last updated: 2026-02-17

Current step id: `P22.1`

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
- `docs/roadmap/owner_split_playbook.md`: owner split (`E*`/`R*`) and research gate (`G*`) contract
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

Current position: **Phase 22 onboarding closure started**

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

#### Phase 12: Process Graph Foundation (Validator-First) (DONE)

Intent:
- Keep runtime core unchanged (in-proc scheduler remains the execution baseline).
- Productize process-graph **specification and validation** before introducing orchestration/runtime automation.
- Pin first bridge to SQLite durable queue with strict semantics.

- `P12.1` Switch SSOT step and define process-graph foundation scope. `DONE`
- `P12.2` Add process-graph model/spec loader (`version: 1`). `DONE`
- `P12.3` Add process-graph validator with SQLite bridge contracts (strict `1 producer + 1 consumer`). `DONE`
- `P12.4` Add standalone validator command (`scripts/proc_graph_validate.py`) + exit-code contract. `DONE`
- `P12.5` Add sample process-graph spec + guide/ops docs sync. `DONE`
- `P12.6` Add unit tests for spec/validator/script contracts. `DONE`
- `P12.7` Record expansion hook for future `N:N` channel semantics (validator-rule relaxation, no schema break). `DONE`

#### Phase 13: Execution Completion Track (E1~E6, Research-Excluded) (DONE)

Intent:
- Complete all implementation work that does not require new research decisions.
- Keep research-track items gated and out of this cycle's runtime changes.
- Finish with reproducible ops/demo quality and explicit ownership boundaries.

- `P13.1` Switch SSOT to execution completion track and open `E1~E6` ownership statuses. `DONE`
- `P13.2` E1: environment/dependency recovery automation (`env_doctor`) + docs. `DONE`
- `P13.3` E2: CI gate hardening (`env/docs/tests/procgraph/demo`). `DONE`
- `P13.4` E3: demo-pack report schema/failure taxonomy hardening. `DONE`
- `P13.5` E4: static demo report visualizer (Markdown/HTML). `DONE`
- `P13.6` E5: scaffold auto-export registration and DX polish. `DONE`
- `P13.7` E6: durable queue reliability regression expansion. `DONE`
- `P13.8` Final docs/mapping/status sync for release readiness. `DONE`

#### Phase 14: Universal UX/TUI Transition (DONE)

Intent:
- De-emphasize camera-centric command surfaces and present a universal stream-ops UX.
- Keep runtime core semantics unchanged while improving operator observability.
- Deliver a read-only Stream TUI first, then leave full GUI/editor work in backlog.

- `P14.1` Switch SSOT to universal UX/TUI transition track and set current step id. `DONE`
- `P14.2` Add `stream_fleet` generic runner and fleet config schema. `DONE`
- `P14.3` Add `stream_monitor` read-only TUI (log+pid based, stdlib only). `DONE`
- `P14.4` Remove `multi_cam` alias and finish stream-centric command surfaces (owner decision). `DONE`
- `P14.5` Add tests and CI coverage for stream fleet/monitor compatibility. `DONE`

#### Phase 15: UX Preset Onboarding (DONE)

Intent:
- Provide a one-command operator experience on top of the stable v2 runtime.
- Keep runtime core semantics unchanged while reducing command/config burden.
- Expose advanced model presets as opt-in (`--experimental`) to keep default UX deterministic.

- `P15.1` Add preset launcher (`scripts/stream_run.py`) and lock default vs experimental preset exposure. `DONE`
- `P15.2` Add profile-aware environment doctor checks (`base`/`yolo`/`webcam`). `DONE`
- `P15.3` Wire docs/index/mapping/status to the new preset surface. `DONE`

#### Phase 16: UX Console + Governance Minimum Baseline (DONE)

Intent:
- Keep UX improvements moving while freezing a stable control boundary for future governance expansion.
- Introduce a thin web console and a local-first control API without changing core runtime semantics.
- Add minimum governance hooks (audit trail + policy snapshot) to reduce future rework.

- `P16.1` Extract shared ops service layer for presets/fleet/monitor/env checks. `DONE` (0bc9520)
- `P16.2` Add stream control API (`scripts/stream_control_api.py`) with local-only default and bearer option. `DONE` (70fb300)
- `P16.3` Add governance minimum baseline (audit logging + policy snapshot endpoint). `DONE` (1b594c1)
- `P16.4` Add React UX console (`apps/stream-console`) for dashboard/presets/fleet/monitor/governance views. `DONE` (9889f2b)
- `P16.5` Sync docs/index/mapping/status and CI for web console and API surface. `DONE` (d8f74fd + docs sync)

#### Phase 17: Governance Hardening + UX Consistency (DONE)

Intent:
- Harden control API governance defaults without changing core runtime semantics.
- Remove UX ambiguity between preset execution output and fleet monitor telemetry.
- Add policy snapshot drift detection in CI to prevent silent governance regression.

- `P17.1` Open phase and align SSOT state/docs. `DONE` (a75340f)
- `P17.2` Enforce bearer for mutating endpoints by default with one-cycle local override switch. `DONE` (714e70c)
- `P17.3` Add audit retention rotation (`size+count`) and expose retention policy in governance snapshots. `DONE` (d07313b)
- `P17.4` Add control policy snapshot generator + CI drift gate. `DONE` (cd0a5f0)
- `P17.5` Clarify fleet-only monitor semantics in stream console UX copy. `DONE` (bed8e2b)
- `P17.6` Finalize docs/index/mapping/status sync for P17 surfaces. `DONE`

#### Phase 18: Onboarding UX + One-Command Console Bootstrap (DONE)

Intent:
- Reduce local onboarding friction by adding a single command surface for API+UI lifecycle.
- Keep control API security defaults while enabling explicit local-lab opt-in for mutations.
- Improve CI/UI reproducibility and document a deterministic quickstart path.

- `P18.1` Open phase and align SSOT step id/state docs for onboarding track. `DONE` (3219920)
- `P18.2` Add console ops service layer (`src/schnitzel_stream/ops/console.py`). `DONE` (baa9a83)
- `P18.3` Add `scripts/stream_console.py` (`up/status/down/doctor`) command surface. `DONE` (bfdabaa)
- `P18.4` Extend `env_doctor` with `console` profile checks (`fastapi`, `uvicorn`, `node`, `npm`). `DONE` (e934da5)
- `P18.5` Add local-console quickstart guide and simplify onboarding docs. `DONE` (11f7a19)
- `P18.6` Add unit tests for console ops/script and env profile coverage. `DONE` (e6fc3b1)
- `P18.7` Harden UI reproducibility (`package-lock` tracked, CI `npm ci`). `DONE` (2e8bf82)
- `P18.8` Final docs/index/mapping/status sync for P18 surfaces. `DONE`

#### Phase 19: Usability Closure (No-Env-First) (DONE)

Intent:
- Minimize environment-variable dependency in day-1 operator flows.
- Keep runtime semantics unchanged while simplifying command surfaces.
- Keep research-track (`R*`/`G*`) work out of this phase.

- `P19.1` Open phase and align SSOT step id/state docs for usability closure track. `DONE` (3502b23)
- `P19.2` Extend preset env override contract for no-env YOLO controls. `DONE` (69e16d6)
- `P19.3` Expand `stream_run` options and add preflight doctor mode. `DONE` (2916d86)
- `P19.4` Split YOLO presets into view/headless profiles and add headless graph. `DONE` (87634e1)
- `P19.5` Align control API and web UI preset options with CLI overrides. `DONE` (d4ebf41, 920d07d)
- `P19.6` Rewrite onboarding docs to option-first execution path. `DONE`
- `P19.7` Add regression coverage for new options and preset split behavior. `DONE` (ff913ed)
- `P19.8` Final docs/index/mapping/status sync for P19 surfaces. `DONE`

#### Phase 20: Graph Authoring UX (CLI Wizard) (DONE)

Intent:
- Lower graph authoring friction with a non-interactive CLI wizard.
- Keep template-driven generation deterministic for scripts and CI usage.
- Keep GUI/block editor explicitly out of scope for this phase (`P21` candidate).

- `P20.1` Open phase and align SSOT step id/state docs for graph authoring track. `DONE` (4878a67)
- `P20.2` Add graph wizard ops service (`src/schnitzel_stream/ops/graph_wizard.py`). `DONE` (1d9432d)
- `P20.3` Add `scripts/graph_wizard.py` command surface (`--list-profiles`, `--profile`, `--validate`). `DONE` (2dd0ed2)
- `P20.4` Add wizard profile metadata + graph template assets. `DONE` (4d3875e)
- `P20.5` Add docs guide and option-first command references for graph wizard. `DONE` (5856c00)
- `P20.6` Add wizard unit coverage (ops/script). `DONE` (1fcd87f)
- `P20.7` Add no-docker CI smoke for graph wizard generation/validation. `DONE` (356d322)
- `P20.8` Final docs/index/mapping/status sync for P20 surfaces. `DONE`

#### Phase 21: Dependency Baseline + Block Editor MVP (DONE)

Intent:
- Lock deterministic dependency/onboarding baseline first (Conda + pip dual path).
- Deliver a block-style graph editor MVP on top of existing control API/runtime semantics.
- Keep research-track and core runtime semantics unchanged.

- `P21.0` Open phase and align SSOT step id/state docs for dependency-first track. `DONE` (1701aaa)
- `P21.1` Add baseline environment artifact (`environment.yml`) and dependency rules. `DONE` (6e4c365)
- `P21.2` Add `bootstrap_env` command and align PowerShell/Bash setup surfaces. `DONE` (6e4c365, 0af6b27)
- `P21.3` Harden `env_doctor` profile guidance to match bootstrap semantics. `DONE` (0af6b27)
- `P21.4` Add graph editor ops service and profile->spec rendering reuse. `DONE` (6d70e1b)
- `P21.5` Extend control API for graph profiles/validate/run flows. `DONE` (03abd59)
- `P21.6` Add web block editor MVP (node/edge/property + YAML import/export + validate/run). `DONE`
- `P21.7` Expand CI gates for dependency/bootstrap/editor surfaces. `DONE`
- `P21.8` Final docs/index/mapping/status sync for P21 surfaces. `DONE`

#### Phase 22: Onboarding Closure (Explicit 3-Step) (NOW)

Intent:
- Finalize the install/start entry surface as an explicit 3-step flow (`bootstrap -> doctor -> up/down`).
- Keep Zero-Env-first operator path stable across PowerShell and Bash.
- Preserve one-cycle compatibility for existing setup surfaces while converging on one standard path.

- `P22.1` Open phase and align SSOT step id/state docs. `NOW`
- `P22.2` Harden `bootstrap_env` contract (`--skip-doctor`, `--json`, deterministic next-action output). `NEXT`
- `P22.3` Align `setup_env.ps1`/`setup_env.sh` option surfaces + one-cycle positional compatibility policy. `NEXT`
- `P22.4` Normalize `env_doctor` and `stream_console` failure taxonomy and recovery guidance. `NEXT`
- `P22.5` Add onboarding smoke regression coverage (`bootstrap`/`setup`/`console`). `NEXT`
- `P22.6` Extend CI onboarding smoke gates for Linux + Windows parity. `NEXT`
- `P22.7` Rewrite onboarding docs to one canonical explicit 3-step path. `NEXT`
- `P22.8` Final mapping/index/status sync for P22 assets. `NEXT`

#### Completion Definition (Engineering Scope Only)

If the planned non-research phases `P22`~`P26` are completed in order, this roadmap is considered **complete for implementable engineering scope**.

Out of this completion definition:
- research-gated items (`R*`, `G*`)
- distributed control-plane runtime
- runtime `N:N` channel semantics
- runtime loop execution semantics beyond current policy

#### Planned Non-Research Finish Track (`P23`~`P26`) (NEXT)

- `P23` Block editor usability hardening: node/edge editing UX, YAML round-trip robustness, clearer validate/run results.
- `P24` Reliability hardening: restart/backlog/ack/timeout regression expansion with deterministic CI coverage.
- `P25` Plugin DX closure: scaffold/template quality, authoring flow reduction, stricter mapping checks.
- `P26` Productization closure: release checklist, command surface freeze, docs/code/CI drift=0 target.

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

- What is the first promoted transport after SQLite bridge (HTTP/MQTT/NATS)?
- How should `N:N` channel semantics define ownership/ack policy in a backward-compatible way?
- What objective readiness criteria should promote foundation validation into runtime orchestration?
- Which `R*` decisions in `docs/roadmap/owner_split_playbook.md` are ready for promotion into execution steps?

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
- 소유권/게이트 계약: `docs/roadmap/owner_split_playbook.md` (`E*`/`R*`/`G*`)
- 완료/역사 계획: git 이력/태그 `pre-legacy-purge-20260216`

### 현재 상태 한눈에 보기

- current step id: `P22.1`
- 전체 위치: **Phase 22 온보딩 완결 트랙 시작**
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
| Phase 3 | DONE (core), LATER (P3.3) | 운영 제어면(메트릭/스로틀) 완료, LLM 컨트롤러는 선택 과제 |
| Phase 4 | DONE | v2 전환 완료 및 레거시 런타임 제거 |
| Phase 5 | DONE | 도메인 중립 네이밍/경계 정리 |
| Phase 6 | DONE | 스트리밍 in-proc 스케줄링/백프레셔 정착 |
| Phase 7 | DONE | payload 이식성 규칙 + `payload_ref` 전략 반영 |
| Phase 8 | DONE | RTSP/Webcam/HTTP/JSONL 등 IO 플러그인 팩 정리 |
| Phase 9 | DONE | 패키징/릴리즈 규율 및 엣지 운영 규약 정리 |
| Phase 10 | DONE | 품질 게이트/CLI 정리/플러그인 DX/데이터 프로파일 하드닝 |
| Phase 11 | DONE | 교수님 시연용 데모 패키지/재현성 고정 |
| Phase 12 | DONE | 프로세스 그래프 스펙/검증기(Validator-First, SQLite 1:1) 도입 완료 |
| Phase 13 | DONE | 연구 제외 실행 완결 트랙(E1~E6) 완료 |
| Phase 14 | DONE | 영상/레거시 뉘앙스 축소, 범용 stream fleet/monitor UX 전환 완료 |
| Phase 15 | DONE | 원커맨드 프리셋 UX + 프로필 기반 환경 진단 + 문서 동기화 완료 |
| Phase 16 | DONE | UX 콘솔 + Control API + 거버넌스 최소선(Audit/Policy Snapshot) 완료 |
| Phase 17 | DONE | 거버넌스 하드닝 + UX 정합성(인증/감사보존/정책드리프트/모니터 의미 명확화) 완료 |
| Phase 18 | DONE | 온보딩 UX + API/UI 원커맨드 콘솔 부트스트랩 완료 |
| Phase 19 | DONE | 환경변수 의존 최소화 + 원커맨드 실행 단순화 |
| Phase 20 | DONE | 그래프 작성 UX(CLI Wizard) 도입 및 템플릿 기반 생성면 구축 완료 |
| Phase 21 | DONE | 의존성 기준선 고정 + 블록코딩 GUI MVP 도입 |
| Phase 22 | NOW | 온보딩/설치 경로 완결(bootstrap/doctor/up-down 명시 3단계 고정) |
| Phase 23 | NEXT | 블록 편집기 사용성 하드닝(편집/검증/실행 UX 정리) |
| Phase 24 | NEXT | 운영 신뢰성 회귀 하드닝(재시작/백로그/ACK/타임아웃) |
| Phase 25 | NEXT | 플러그인 DX 마감(스캐폴드/템플릿/가이드 완성도) |
| Phase 26 | NEXT | 제품화 마감(릴리즈 체크리스트/명령면 고정/드리프트 0) |

### 완성 기준(구현 범위 한정)

`P22`~`P26`을 순서대로 완료하면 이 로드맵은 **연구 제외 구현 범위에서 완성**으로 본다.

완성 범위에서 제외:
- 연구 게이트 항목(`R*`, `G*`)
- 분산 컨트롤플레인 런타임
- `N:N` 채널 런타임 의미론
- 현재 정책을 넘는 루프 런타임 의미론

### 현재 우선순위

1. `P22.2`~`P22.4`로 bootstrap/doctor/console 계약을 명시 3단계로 고정한다
2. `P22.5`~`P22.6`으로 Linux+Windows 온보딩 회귀/CI 게이트를 동급으로 잠근다
3. `P22.7`~`P22.8`로 문서 단일 경로화와 매핑 동기화를 마무리한다

### 레거시 관련 기준

- 레거시 제거 계획/체크리스트는 워킹 트리에서 제거되었으며 git 이력/태그로 관리한다.
- 참조: `pre-legacy-purge-20260216`

### 검증 상태

- 로컬 실행 완료: `python3 -m compileall -q src tests`
- 로컬 미실행: `pytest` (개발 의존성 설치 필요, push 시 CI 검증 권장)

### 열린 쟁점

1. SQLite 1:1 foundation에서 `N:N`으로 확장할 때 ack ownership을 어떻게 고정할지
2. 분산 실행 승격 시 transport/오케스트레이션 경계를 어디서 나눌지(`B2`, `B3`)
3. `docs/roadmap/owner_split_playbook.md`의 `R*` 결정 중 어떤 항목을 실행 단계로 승격할지
4. `P3.3`/연구 트랙(`R1~R3`) 재개 시점을 어떤 운영 신호로 판단할지
