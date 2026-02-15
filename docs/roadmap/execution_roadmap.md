# Execution Roadmap (Platform Pivot SSOT)

Last updated: 2026-02-15

Current step id: `P9.2`

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
- `GATED`: blocked by an explicit precondition (ex: deprecation window)

#### Phase 0: Entrypoint SSOT + Strangler (DONE ~100%)

- `P0.1` Cross-platform LF canonical (`.gitattributes`). `DONE` (291874c)
- `P0.2` Introduce `schnitzel_stream` core skeleton. `DONE` (287abde)
- `P0.3` Phase 0 job spec + legacy job runner. `DONE` (29cb3ed)
- `P0.4` New CLI entrypoint `python -m schnitzel_stream`. `DONE` (5cd6c43)
- `P0.5` Migrate tests/scripts/Docker/docs, disable legacy CLI. `DONE` (c729fb9, 62786b7, aa8d515)
- `P0.6` SSOT docs for pivot (architecture/plan/support matrix/roadmap refinement). `DONE` (5e30823, 151676c, 4f1ab87, 92567af)
- `P0.7` StreamPacket contract SSOT + references. `DONE` (f34f876)

Current position: **Phase 9** (`P9.2` is NOW; `P4.5` remains gated by the deprecation window; `P3.3` remains optional)

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

#### Phase 3: Ops Control Surface (DONE core; research optional)

Intent:
- Phase 3 is **not** a multi-camera orchestrator or a distributed scheduler.
- Phase 3 is the minimal "control surface" required to run safely on edge: metrics/health contracts and policy-driven tuning hooks.

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
- `P4.5` Remove legacy runtime from main tree after the deprecation window. `GATED` (>= 90 days after `P4.3`)

#### Phase 5: Platform Generalization (Domain-Neutral) (DONE)

Intent:
- Phase 5 makes the repo feel like a **universal stream platform**, not a CCTV project:
  - domain-specific things remain supported, but they live behind plugin boundaries or under `legacy/`
  - docs/examples naming should be domain-neutral by default

- `P5.1` Docs + examples taxonomy cleanup (platform vs legacy) and naming de-CCTVization. `DONE` (48455a1, 41e9439, f389234)
  - DoD:
    - Top-level entry docs (`README.md`, `PROMPT*.md`, `docs/index.md`) clearly separate `platform` vs `legacy`.
    - Legacy-only docs/specs are explicitly named `legacy_*` or moved under `docs/legacy/`.
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

#### Phase 9: Cross-Platform Packaging + Release Discipline (NOW)

- `P9.1` Finalize support matrix and packaging lanes (Docker + no-Docker). `DONE` (36a588c, 166b95e)
  - DoD:
    - documented target list (OS/arch) and lane policy
    - CI verifies at least one "no-Docker" lane (`pip` + venv) end-to-end
    - optional: multi-arch Docker build lane
- `P9.2` Edge ops conventions (paths, service mode, logs) hardened. `NOW`

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
- What are the OS-specific service-mode and default path conventions for long-running edge deployments?

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

현재 위치: **Phase 9** (`P9.2`가 NOW이며, `P4.5`는 deprecation window로 GATED 상태, `P3.3`는 optional)

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

#### Phase 3: 운영 제어 표면 (코어는 DONE, 연구/옵션 분리)

의도(Intent):
- Phase 3는 멀티 카메라 오케스트레이터나 분산 스케줄러가 **아닙니다**.
- Phase 3는 엣지에서 안전하게 돌리기 위한 최소 “제어 표면”입니다: metrics/health 계약 + 정책 기반 튜닝 훅.

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
- `P4.5` Remove legacy runtime from main tree after the deprecation window. `GATED` (>= 90 days after `P4.3`)

#### Phase 5: 플랫폼 범용화(도메인 중립) (DONE)

의도(Intent):
- Phase 5의 목표는 레포가 **범용 스트림 플랫폼**처럼 보이고 동작하게 만드는 것입니다.
  - 도메인 특화 기능은 계속 지원하되, 플러그인 경계 뒤로 보내거나 `legacy/`로 격리합니다.
  - 문서/예시 네이밍은 기본적으로 도메인 중립이어야 합니다.

- `P5.1` 문서 + 예시 그래프 분류/정리(platform vs legacy) 및 네이밍 de-CCTVization. `DONE` (48455a1, 41e9439, f389234)
  - DoD:
    - 최상위 진입 문서(`README.md`, `PROMPT*.md`, `docs/index.md`)에서 `platform`과 `legacy`가 명확히 분리되어야 합니다.
    - 레거시 전용 문서/스펙은 `legacy_*`로 명시하거나 `docs/legacy/`로 이동합니다.
    - 기본/예시 v2 그래프는 레거시 예시가 아닌 한 CCTV 네이밍을 피합니다.
- `P5.2` IO(소스/싱크) 및 정책 노드의 플러그인 경계 강화. `DONE` (05719be, 5925f2e)
  - DoD:
    - RTSP/webcam/file 입력은 코어와 결합되지 않은 `source` 플러그인으로만 제공됩니다.
    - backend/JSONL/stdout 출력은 `sink` 플러그인으로만 제공됩니다.
    - `schnitzel_stream` 코어는 CCTV/백엔드 스키마 가정을 포함하지 않습니다(계약은 `StreamPacket`).

#### Phase 6: 스트리밍 in-proc 런타임 의미론 (DONE)

문제:
- 현재 in-proc runner는 source를 끝까지 실행한 다음에 downstream 노드를 실행합니다. 작은 데모엔 괜찮지만 RTSP/webcam 같은 스트리밍 소스나 큰 파일에서는 메모리/지연 문제가 생깁니다.

의도(Intent):
- strict DAG 안전성을 기본으로 유지하면서, 런타임을 “배치 DAG 평가기”에서 “스트리밍 패킷 스케줄러”로 진화시킵니다.

- `P6.1` 인터리빙 스케줄러: 패킷을 점진적으로 처리(다운스트림 실행 전 무한 버퍼링 금지). `DONE` (282a74a)
  - DoD:
    - 소스가 무한 iterator여도 다운스트림이 굶지 않습니다(starvation 없음).
    - 패킷이 흐르면서 처리됩니다(바운디드 큐).
    - 결정적 stop 조건(`--max-packets` / 시간 예산 / throttle policy)이 존재합니다.
- `P6.2` 백프레셔 + 큐 정책: bounded inbox, drop/slowdown 의미론, 메트릭. `DONE` (8e1b5db)
  - DoD:
    - 노드별 inbox limit 설정 가능
    - drop/backpressure 이벤트가 메트릭으로 남음

#### Phase 7: Payload 이식성 + Transport Lane (DONE)

의도(Intent):
- “어떤 데이터가 경계를 넘을 수 있는가”를 명시합니다(in-proc 객체 vs durable/IPC/network).

- `P7.1` payload 이식성 정책 + validator 강제. `DONE` (18ddb75)
  - DoD:
    - non-portable payload(예: raw frame)가 durable/network 경로로 라우팅되면 validate에서 실패합니다.
    - durable queue 노드는 blob/handle 전략이 나오기 전까지 JSON-only임을 문서화합니다.
- `P7.2` 큰/바이너리 payload(프레임/오디오)용 handle 전략(`payload_ref`). `DONE` (c4d40bf)
  - DoD:
    - `StreamPacket`이 file/shm/uri 기반 portable reference를 지원하며, lifecycle 규칙이 명확합니다.

#### Phase 8: IO 플러그인 팩(RTSP/Webcam/HTTP 등) (DONE)

의도(Intent):
- RTSP와 “backend”는 교체 가능한 어댑터입니다. 플랫폼은 최소 배터리를 제공하고, 배포 환경은 필요한 어댑터를 가져옵니다.

- `P8.1` RTSP source 플러그인(reconnect/backoff) + 테스트 + 데모 그래프. `DONE` (8cf52e8, 471ff6c)
- `P8.2` Webcam source 플러그인 + 테스트 + 데모 그래프. `DONE` (3d9e889, 9886e63)
- `P8.3` HTTP sink 플러그인(idempotency + retry 정책) + 테스트 + 데모 그래프. `DONE` (2d7442c, 83baaad)
- `P8.4` JSONL/file sink 플러그인 + 테스트. `DONE` (983be3f, c9f831e)

#### Phase 9: 크로스플랫폼 패키징 + 릴리즈 규율 (NOW)

- `P9.1` 지원 매트릭스/패키징 레인(Docker + no-Docker) 확정. `DONE` (36a588c, 166b95e)
  - DoD:
    - 타겟(OS/arch)과 레인 정책이 문서화되어야 함
    - CI가 최소 1개의 no-Docker 레인(pip+venv)을 E2E로 검증
    - 옵션: multi-arch Docker 빌드 레인
- `P9.2` 엣지 운영 규약(경로/서비스 모드/로그) 강화. `NOW`

#### 연구 트랙(크리티컬 패스 아님)

의도(Intent):
- 오케스트레이터/LLM 컨트롤러는 논문급 과제가 될 수 있으므로, 코어 플랫폼이 안정화되기 전에는 크리티컬 패스에서 제외합니다.

- `R1` validator-only를 넘는 cycle 실행 의미론(가드레일 포함). `LATER`
- `R2` 멀티 카메라 오케스트레이터/프로세스 매니저/추론 서버 아키텍처. `LATER`
- `R3` LLM/controller 레이어(사용자 승인 기반). `LATER`

### 검증

- 실행됨(로컬): `python3 -m compileall -q src tests`
- 실행 안 함(로컬): `pytest` (venv deps 필요; push 시 CI가 강제)

### 미해결 질문

- Phase 1 런타임 실행 모델은 무엇인가?
  - push vs pull, 배치/윈도우, 백프레셔 의미론
- CCTV에 과적합하지 않으면서도 invalid graph를 막는 최소 port/type 시스템은 무엇인가?
- 장기 실행 엣지 배포에서 OS별 서비스 모드 및 기본 경로 규약을 어떻게 표준화할 것인가?
