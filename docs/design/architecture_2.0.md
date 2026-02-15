# Architecture 2.0 (PROVISIONAL)

Last updated: 2026-02-13

## English

Intent:
- This document is **provisional**. The platform pivot is in progress and the roadmap may change.
- Phase 0 intentionally runs the legacy `ai.pipeline` runtime through the new `schnitzel_stream` entrypoint (Strangler pattern).

### Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/roadmap/migration_plan_phase0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Define the platform boundaries and the Phase 0/1 execution model for the universal stream platform namespace `schnitzel_stream`.
- **Non-scope**: Finalized DAG semantics, distributed scheduling, and any promise of stable public API beyond the CLI entrypoint in Phase 0.

### Boundary Map

- **Platform core (new)**: `src/schnitzel_stream/`
  - CLI entrypoint: `python -m schnitzel_stream` (`src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py`)
  - Minimal graph spec: `src/schnitzel_stream/graph/spec.py` (Phase 0 job indirection)
  - Plugin loading policy: `src/schnitzel_stream/plugins/registry.py` (allowlist by default)
  - Core abstractions (early): `src/schnitzel_stream/packet.py`, `src/schnitzel_stream/node.py`
- **Legacy runtime (kept for Phase 0)**: `legacy/ai/` (import path remains `ai.*` via `src/ai` shim)
  - The "AI pipeline" remains implemented under `ai.*` modules.
  - Execution is routed via `schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob`.

### Critical Dependencies

- Python: **3.11** baseline (CI matrix).
- `omegaconf`: config + graph spec parsing.
- OpenCV: optional at runtime (visualization / frame decode paths); keep GUI as an opt-in flag.
- OS facilities: filesystem paths, networking, and signals (best-effort on Windows).

### Evolution Constraints

- CLI stability: `python -m schnitzel_stream` must remain the stable entrypoint as the platform evolves.
- Determinism: default config paths must not depend on CWD (tests/Docker/edge must behave the same).
- Side effects: keep I/O in adapters/jobs; core abstractions must remain reusable without RTSP/backend assumptions.
- Plugin safety: default should be production-safe (allowlist); dev can override via env explicitly.

### Risks (P0–P3)

- **P0**: Running arbitrary code via plugin loading is a security risk if policy is too permissive.
- **P1**: Phase 0 job-only graph spec can become accidental long-term API; must version early.
- **P2**: Cross-platform behavior drift (paths, signals, OpenCV, RTSP transports) can fragment edge support.
- **P3**: Doc/code drift during pivot (legacy docs still present); requires explicit SSOT mapping and updates.

### Mismatches (path)

- None found.

### Fix Plan

1. Phase 0 (now): stabilize the new entrypoint and keep legacy job execution reliable.
2. Phase 1: introduce a real DAG runtime that executes `Node` graphs with `StreamPacket` as the only contract.
3. Phase 1+: migrate legacy capabilities into plugins/nodes incrementally (sources, sensors, emitters, zones).
4. Phase 2+: add static graph validation (ports/types/transport compatibility) and policy-driven runtime tuning.

### Verification

- Executed: `python3 -m compileall -q src/schnitzel_stream`.
- Not executed: end-to-end runtime validation on real RTSP devices (hardware not available here).

### Open Questions

- Packaging strategy for "almost all edges": what is the official support matrix (Windows/macOS/Linux, amd64/arm64, Jetson/GPU)?
- How do we represent large payloads (frames) in StreamPacket without forcing serialization/copies?
- Where should long-lived state live (State Node vs external store vs blackboard), and what is the failure model?

---

## 한국어

의도(Intent):
- 이 문서는 **잠정(PROVISIONAL)** 입니다. 플랫폼 피벗이 진행 중이며 로드맵은 바뀔 수 있습니다.
- Phase 0는 의도적으로(Strangler 패턴) 새 엔트리포인트 `schnitzel_stream`를 통해 레거시 `ai.pipeline` 런타임을 실행합니다.

### 요약

- **참조 SSOT 문서**: `docs/roadmap/strategic_roadmap.md`, `docs/roadmap/migration_plan_phase0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **범위**: 범용 스트림 플랫폼 네임스페이스 `schnitzel_stream`의 경계와 Phase 0/1 실행 모델을 정의합니다.
- **비범위**: 최종 DAG 의미론, 분산 스케줄링, Phase 0에서 CLI 엔트리포인트를 넘어서는 안정적인 공개 API 보장.

### 경계 맵 (Boundary Map)

- **플랫폼 코어(신규)**: `src/schnitzel_stream/`
  - CLI 엔트리포인트: `python -m schnitzel_stream` (`src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py`)
  - 최소 그래프 스펙: `src/schnitzel_stream/graph/spec.py` (Phase 0 job indirection)
  - 플러그인 로딩 정책: `src/schnitzel_stream/plugins/registry.py` (기본 allowlist)
  - 코어 추상화(초기): `src/schnitzel_stream/packet.py`, `src/schnitzel_stream/node.py`
- **레거시 런타임(Phase 0 호환 유지)**: `legacy/ai/` (import 경로는 `src/ai` shim을 통해 `ai.*` 유지)
  - "AI pipeline"은 `ai.*` 모듈 아래에 유지됩니다.
  - 실행은 `schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob`로 라우팅됩니다.

### 핵심 의존성 (Critical Dependencies)

- Python: **3.11** (CI 기준).
- `omegaconf`: config + graph spec 파싱.
- OpenCV: 런타임에서 선택(optional) (시각화/프레임 디코드 경로). GUI는 opt-in 플래그로 유지.
- OS 기능: 파일시스템 경로, 네트워킹, 시그널(Windows는 best-effort).

### 진화 제약 (Evolution Constraints)

- CLI 안정성: `python -m schnitzel_stream`는 플랫폼 진화 과정에서도 안정 엔트리포인트로 유지되어야 합니다.
- 결정성: 기본 config 경로는 CWD에 의존하지 않아야 합니다(테스트/Docker/엣지 동일).
- 부작용(Side effects): I/O는 adapter/job로 격리하고, 코어는 RTSP/백엔드 가정 없이 재사용 가능해야 합니다.
- 플러그인 안전: 기본은 프로덕션 안전(allowlist)이어야 하며, dev에서만 env로 명시적으로 완화합니다.

### 리스크 (P0–P3)

- **P0**: 플러그인 로딩 정책이 과도하게 느슨하면 임의 코드 실행 위험이 큽니다.
- **P1**: Phase 0의 job-only 그래프 스펙이 의도치 않게 장기 API가 될 수 있으므로, 초기부터 버전 관리가 필요합니다.
- **P2**: 크로스플랫폼 동작 차이(경로/시그널/OpenCV/RTSP)가 엣지 지원을 분절시킬 수 있습니다.
- **P3**: 피벗 중 문서/코드 드리프트(레거시 문서 잔존)가 발생할 수 있으므로 SSOT 매핑과 업데이트가 필요합니다.

### 불일치(경로)

- 발견된 불일치 없음.

### 실행 계획

1. Phase 0(현재): 새 엔트리포인트를 안정화하고 레거시 job 실행 신뢰성을 유지합니다.
2. Phase 1: `StreamPacket`만을 계약으로 사용하는 `Node` 그래프 DAG 런타임을 도입합니다.
3. Phase 1+: 레거시 기능을 플러그인/노드로 점진적으로 이전합니다(source/sensor/emitter/zones 등).
4. Phase 2+: 정적 그래프 검증(ports/types/transport 호환성)과 정책 기반 런타임 튜닝을 추가합니다.

### 검증

- 실행됨: `python3 -m compileall -q src/schnitzel_stream`
- 실행 안 함: 실제 RTSP 장치 기반 E2E 런타임 검증(하드웨어 미보유)

### 미해결 질문

- “거의 모든 엣지”를 위한 패키징 전략: 공식 지원 매트릭스(Windows/macOS/Linux, amd64/arm64, Jetson/GPU)는?
- StreamPacket에서 큰 payload(프레임)를 직렬화/복사 강제 없이 어떻게 표현할 것인가?
- 장수 상태(long-lived state)는 어디에 둘 것인가(State Node vs 외부 store vs blackboard)? 실패 모델은?
