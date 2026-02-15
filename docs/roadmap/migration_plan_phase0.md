# Phase 0 Migration Plan (Universal Platform SSOT)

Last updated: 2026-02-14

## English

Note:
- Phase 0 is complete. This document is kept as historical context.
- Current default graph is v2: `configs/graphs/dev_cctv_e2e_mock_v2.yaml` (see `docs/roadmap/execution_roadmap.md`).

### Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Phase 0 "Strangler" migration to make `python -m schnitzel_stream` the single supported runtime entrypoint, while executing the existing `ai.pipeline` runtime as a legacy job.
- **Non-scope**: Full DAG runtime, distributed execution, and finalized long-term StreamPacket schema (these remain provisional).

### Risks (P0–P3)

- **P0**: Existing users/automation still calling `python -m ai.pipeline` will hard-fail.
- **P1**: Phase 0 graph spec is job-only; config validation is intentionally limited and may allow invalid future graphs.
- **P2**: Plugin allowlist may block experimental adapters in dev environments.
- **P3**: Cross-platform line ending drift (CRLF/LF) can create noisy diffs and operational surprises.

### Mismatches (path)

- None found.

### Fix Plan

1. **Cross-platform hygiene**: enforce canonical LF line endings with `.gitattributes` to prevent CRLF noise in diffs and containers.
2. **New platform package**: introduce `src/schnitzel_stream/` as the universal platform namespace (StreamPacket/Node/PluginPolicy).
3. **Phase 0 graph spec**: add minimal `GraphSpec` loader (YAML) with explicit versioning.
4. **Phase 0 legacy job**: implement `LegacyAIPipelineJob` that runs `ai.pipeline` runtime via the new platform entrypoint.
5. **New CLI**: implement `python -m schnitzel_stream` as the stable entrypoint.
   - Phase 0 default graph was `configs/graphs/legacy_pipeline.yaml` (v1 job graph).
   - Phase 4 default graph is `configs/graphs/dev_cctv_e2e_mock_v2.yaml` (v2 node graph).
6. **Test migration**: switch subprocess integration/regression tests from `-m ai.pipeline` to `-m schnitzel_stream`.
7. **Disable legacy CLI**: keep `legacy/ai/pipeline/__main__.py` but make it fail-fast with a clear migration message.
8. **Ops + docs migration**: update Docker CMD, scripts, and docs to reference `python -m schnitzel_stream` instead of `python -m ai.pipeline`.
9. **SSOT documents (this change-set)**: add `docs/design/architecture_2.0.md`, update `docs/index.md` and `docs/specs/legacy_pipeline_spec.md` to reflect the new entrypoint and Phase 0 indirection.

### Verification

- Executed:
  - `python3 -m compileall -q src/schnitzel_stream`
  - `python3 -m compileall -q src scripts tests`
- Not executed:
  - `pytest` (local runtime/tooling not available in this environment; CI should validate on push).

### Open Questions

- GraphSpec evolution: job-only (Phase 0) -> DAG runtime (Phase 1+). What is the versioning and backward-compat policy?
- Cross-platform packaging: Docker-only vs pip/venv vs PyInstaller. What is the official support matrix (OS/arch/GPU)?
- StreamPacket contract: typed payload vs `Any`, serialization boundaries, and handling of large/binary frame payloads.
- Security posture for plugins: what is the prod policy for plugin loading and distribution?

---

## 한국어

참고:
- Phase 0는 완료되었습니다. 이 문서는 역사적 맥락을 위해 유지합니다.
- 현재 기본 그래프는 v2 입니다: `configs/graphs/dev_cctv_e2e_mock_v2.yaml` (자세한 상태는 `docs/roadmap/execution_roadmap.md`).

### 요약

- **참조 SSOT 문서**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **범위**: `python -m schnitzel_stream`를 유일한 지원 엔트리포인트로 만들면서, 기존 `ai.pipeline` 런타임은 레거시 job으로 실행하는 Phase 0(스트랭글러) 마이그레이션 계획.
- **비범위**: 완전한 DAG 런타임, 분산 실행, 장기적으로 확정된 StreamPacket 스키마(모두 잠정/단계적).

### 리스크 (P0–P3)

- **P0**: 기존 사용자/자동화가 여전히 `python -m ai.pipeline`을 호출하면 즉시 실패합니다.
- **P1**: Phase 0 그래프 스펙은 job-only이며, 설정 검증은 의도적으로 제한되어 향후 invalid graph를 허용할 수 있습니다.
- **P2**: 플러그인 allowlist 정책이 dev 환경의 실험적 어댑터를 막을 수 있습니다.
- **P3**: CRLF/LF 라인엔딩 드리프트가 운영/컨테이너/리뷰에서 노이즈를 유발할 수 있습니다.

### 불일치(경로)

- 발견된 불일치 없음.

### 실행 계획

1. **크로스플랫폼 위생**: `.gitattributes`로 LF 라인엔딩을 표준화해 CRLF 노이즈를 방지합니다.
2. **새 플랫폼 패키지**: `src/schnitzel_stream/`를 범용 플랫폼 네임스페이스(StreamPacket/Node/PluginPolicy)로 도입합니다.
3. **Phase 0 그래프 스펙**: 명시적 버전이 있는 최소 `GraphSpec`(YAML) 로더를 추가합니다.
4. **Phase 0 레거시 job**: 새 엔트리포인트에서 `ai.pipeline`을 실행하는 `LegacyAIPipelineJob`을 구현합니다.
5. **새 CLI**: 안정 엔트리포인트로 `python -m schnitzel_stream`를 제공합니다.
   - Phase 0 기본 그래프는 `configs/graphs/legacy_pipeline.yaml`(v1 job graph)였습니다.
   - Phase 4 기본 그래프는 `configs/graphs/dev_cctv_e2e_mock_v2.yaml`(v2 node graph)입니다.
6. **테스트 마이그레이션**: subprocess 기반 통합/회귀 테스트 엔트리포인트를 `-m ai.pipeline`에서 `-m schnitzel_stream`로 전환합니다.
7. **레거시 CLI 비활성화**: `legacy/ai/pipeline/__main__.py`는 유지하되, 명확한 마이그레이션 메시지로 fail-fast 합니다.
8. **운영/문서 마이그레이션**: Docker CMD, 스크립트, 문서에서 `python -m ai.pipeline` 대신 `python -m schnitzel_stream`를 참조하도록 수정합니다.
9. **SSOT 문서(본 변경셋)**: `docs/design/architecture_2.0.md`를 추가하고, `docs/index.md` 및 `docs/specs/legacy_pipeline_spec.md`를 업데이트해 새 엔트리포인트와 Phase 0 우회(indirection)를 반영합니다.

### 검증

- 실행됨:
  - `python3 -m compileall -q src/schnitzel_stream`
  - `python3 -m compileall -q src scripts tests`
- 실행 안 함:
  - `pytest` (이 환경에서는 로컬 런타임/툴링이 없을 수 있으며, push 시 CI가 검증해야 함)

### 미해결 질문

- GraphSpec 진화: job-only(Phase 0) -> DAG 런타임(Phase 1+). 버전/하위호환 정책은?
- 크로스플랫폼 패키징: Docker-only vs pip/venv vs PyInstaller. 공식 지원 매트릭스(OS/arch/GPU)는?
- StreamPacket 계약: typed payload vs `Any`, 직렬화 경계, 큰/바이너리 frame payload 처리 방법은?
- 플러그인 보안: 프로덕션에서의 플러그인 로딩/배포 정책은?
