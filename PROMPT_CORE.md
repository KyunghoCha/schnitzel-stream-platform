# Handoff Prompt (schnitzel-stream-platform: Core / Platform Pivot)

## English

You are continuing work on the **universal stream processing platform** repo `schnitzel-stream-platform`.

This `PROMPT_CORE.md` defines the rules and the current migration status for the **platform pivot**.
Legacy CCTV/AI runtime lives under `src/ai/`, but execution is routed through the new platform entrypoint.

### Repo Purpose

- **Universal Stream Platform**: a lightweight and extensible runtime for heterogeneous streams (Video, Sensor, Audio, Robot Telemetry).
- **Edge-First**: runs on small edge devices and scales upward without changing the core contract.
- **Strangler Migration**: keep the legacy runtime reliable while incrementally introducing the new SSOT architecture.

### Current Status (2026-02-13)

- **Canonical entrypoint**: `python -m schnitzel_stream` (Phase 0 CLI + default graph spec).
- **Phase 0 graph spec**: `configs/graphs/legacy_pipeline.yaml` -> job indirection.
- **Legacy job runner**: `schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob` executes the existing `ai.pipeline` runtime.
- **Legacy CLI disabled**: `python -m ai.pipeline` fail-fast with a clear migration message.
- **Cross-platform hygiene**: `.gitattributes` enforces LF canonical line endings to avoid CRLF noise.
- **Tests migrated**: subprocess integration/regression tests now call `-m schnitzel_stream`.

### Working Principles (Execution Standard)

1. **SSOT discipline**: always state which document(s) are authoritative for the change.
2. **End-to-end integrity**: code, docs, and tests move together when behavior changes.
3. **Strangler safety**: Phase 0 must keep legacy runtime behavior stable; prefer adapters/wrappers over rewrites.
4. **Cross-platform determinism**: avoid CWD-dependent paths; use repo-root resolution; prefer `pathlib`.
5. **Plugin safety**: default plugin policy must be allowlist-based; dev-only overrides must be explicit.
6. **"Intent:" comments**: when behavior is deliberately non-obvious (fallbacks, tradeoffs, temporary constraints), add an `Intent:` comment near the code.
7. **Incremental commits**: keep commits small and coherent (entrypoint/tests/docs together when they must).

### Key Docs (read first)

1. `docs/roadmap/strategic_roadmap.md` (Vision / target architecture)
2. `docs/roadmap/migration_plan_phase0.md` (Phase 0 plan)
3. `docs/design/architecture_2.0.md` (Provisional platform architecture)
4. `docs/implementation/90-packaging/entrypoint/design.md` (Entrypoint packaging)
5. `docs/contracts/protocol.md` (Event schema; legacy runtime contract)
6. `docs/specs/pipeline_spec.md` (Legacy pipeline behavior via `schnitzel_stream`)

### Immediate Next Steps (Provisional)

1. Define the Phase 1 DAG runtime contract (ports/types/validation) without breaking the Phase 0 job runner.
2. Decide an official edge support matrix (OS/arch/GPU) and packaging strategy (Docker vs pip/venv vs standalone).
3. Start migrating legacy capabilities into explicit platform plugins/nodes (sources, emitters, sensor adapters).

### Context Budget Rule

If you are running low on context/token budget, update `PROMPT_CORE.md` with:
- what was completed (with commit refs if available),
- what remains (ordered by risk/impact),
- open questions and decisions needed next.

---

## 한국어

당신은 **범용 스트림 처리 플랫폼** 레포 `schnitzel-stream-platform` 작업을 이어서 진행합니다.

이 `PROMPT_CORE.md`는 **플랫폼 피벗**의 규칙과 현재 마이그레이션 상태를 정의합니다.
레거시 CCTV/AI 런타임은 `src/ai/`에 유지되지만, 실행은 새로운 플랫폼 엔트리포인트를 통해 라우팅됩니다.

### 레포 목적

- **범용 스트림 플랫폼**: 영상/센서/오디오/로봇 텔레메트리 등 이기종 스트림을 처리하는 경량/확장 가능한 런타임.
- **엣지 우선**: 작은 엣지 디바이스부터 상위 스케일까지 코어 계약을 바꾸지 않고 확장.
- **Strangler 마이그레이션**: 레거시 런타임 신뢰성을 유지하면서 SSOT 아키텍처를 점진적으로 도입.

### 현재 상태 (2026-02-13)

- **표준 엔트리포인트**: `python -m schnitzel_stream` (Phase 0 CLI + 기본 그래프 스펙).
- **Phase 0 그래프 스펙**: `configs/graphs/legacy_pipeline.yaml` (job 간접화).
- **레거시 job 실행기**: `schnitzel_stream.jobs.legacy_ai_pipeline:LegacyAIPipelineJob`가 기존 `ai.pipeline` 런타임을 실행.
- **레거시 CLI 비활성화**: `python -m ai.pipeline`는 명확한 마이그레이션 메시지와 함께 fail-fast.
- **크로스 플랫폼 위생**: `.gitattributes`로 LF 라인엔딩을 정규화(CRLF 노이즈 방지).
- **테스트 마이그레이션**: subprocess 통합/회귀 테스트가 `-m schnitzel_stream`를 사용.

### 작업 원칙 (실행 표준)

1. **SSOT 준수**: 변경 시 어떤 문서가 기준인지 항상 명시한다.
2. **E2E 정합성**: 동작 변경 시 코드/문서/테스트를 함께 갱신한다.
3. **Strangler 안전성**: Phase 0에서는 레거시 런타임 동작 안정성을 최우선으로 유지한다(리라이트보다 래퍼/어댑터 우선).
4. **크로스 플랫폼 결정성**: CWD 의존 경로 금지, repo-root 기준 경로 해석, `pathlib` 우선.
5. **플러그인 안전성**: 기본 정책은 allowlist 기반이어야 하며, dev-only 예외는 env로 명시한다.
6. **"Intent:" 주석**: 비자명한 동작(폴백/트레이드오프/임시 제약)은 코드 근처에 `Intent:` 주석으로 명확히 남긴다.
7. **단계적 커밋**: 커밋은 작고 응집력 있게(필요 시 엔트리포인트/테스트/문서를 같은 커밋으로 묶는다).

### 우선 읽을 문서

1. `docs/roadmap/strategic_roadmap.md` (비전 / 목표 아키텍처)
2. `docs/roadmap/migration_plan_phase0.md` (Phase 0 계획)
3. `docs/design/architecture_2.0.md` (플랫폼 아키텍처, 잠정)
4. `docs/implementation/90-packaging/entrypoint/design.md` (엔트리포인트/패키징)
5. `docs/contracts/protocol.md` (이벤트 스키마; 레거시 계약)
6. `docs/specs/pipeline_spec.md` (레거시 파이프라인 동작, `schnitzel_stream`로 실행)

### 즉시 다음 단계 (잠정)

1. Phase 0 job runner를 깨지 않으면서 Phase 1 DAG 런타임 계약(포트/타입/검증)을 정의한다.
2. 엣지 지원 매트릭스(OS/아키텍처/GPU)와 배포 전략(Docker vs pip/venv vs 단일 실행 파일)을 확정한다.
3. 레거시 기능을 플랫폼 플러그인/노드로 점진 이전한다(소스/에미터/센서 어댑터 등).

### 컨텍스트 예산 규칙

토큰/컨텍스트 예산이 부족해지면 `PROMPT_CORE.md`에 다음을 갱신한다:
- 완료한 내용(가능하면 commit ref 포함),
- 남은 작업(리스크/임팩트 순),
- 남은 질문/다음 의사결정 항목.

