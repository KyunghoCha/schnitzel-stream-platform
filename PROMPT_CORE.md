# Handoff Prompt Core (schnitzel-stream-platform)

Last updated: 2026-02-16

## English

You are working on the universal stream platform repository `schnitzel-stream-platform`.

Execution SSOT:
- `docs/roadmap/execution_roadmap.md`

Current status:
- Current step id: `P3.3` (optional research/control-plane track)
- Core platform phases (`P0`~`P10`) are complete on `main`
- Legacy runtime/docs were removed from the working tree
- Historical legacy state can be inspected via tag `pre-legacy-purge-20260216`

Working rules:
1. Keep SSOT discipline: update docs/code/tests together when behavior changes.
2. Use plugin-first boundaries (`source`, `node`, `sink`) and preserve contract-first design (`StreamPacket`).
3. Maintain compatibility/safety checks through validators before runtime execution.
4. Add `Intent:` comments where behavior is deliberately non-obvious.
5. Keep commits incremental and coherent.

Primary docs to read before major changes:
1. `docs/index.md`
2. `docs/roadmap/execution_roadmap.md`
3. `docs/roadmap/strategic_roadmap.md`
4. `docs/contracts/stream_packet.md`
5. `docs/implementation/runtime_core.md`
6. `docs/reference/doc_code_mapping.md`

Context budget rule:
- If context is low, update this file with completed work, remaining work, and open decisions.

---

## 한국어

당신은 `schnitzel-stream-platform` 범용 스트림 플랫폼 레포를 작업한다.

실행 SSOT:
- `docs/roadmap/execution_roadmap.md`

현재 상태:
- 현재 step id: `P3.3` (옵션 연구/컨트롤플레인 트랙)
- 코어 플랫폼 단계(`P0`~`P10`)는 `main` 기준 완료
- 레거시 런타임/문서는 워킹 트리에서 제거됨
- 과거 레거시 상태는 태그 `pre-legacy-purge-20260216`에서 확인

작업 규칙:
1. SSOT를 기준으로 코드/문서/테스트를 함께 갱신한다.
2. 플러그인 경계(`source`, `node`, `sink`)와 계약 중심(`StreamPacket`) 설계를 유지한다.
3. 런타임 실행 전 validator로 호환성/안전성 검사를 유지한다.
4. 의도적으로 비자명한 동작에는 `Intent:` 주석을 남긴다.
5. 커밋은 작고 응집력 있게 나눈다.

큰 변경 전에 우선 읽을 문서:
1. `docs/index.md`
2. `docs/roadmap/execution_roadmap.md`
3. `docs/roadmap/strategic_roadmap.md`
4. `docs/contracts/stream_packet.md`
5. `docs/implementation/runtime_core.md`
6. `docs/reference/doc_code_mapping.md`

컨텍스트 예산 규칙:
- 컨텍스트가 부족하면 이 파일에 완료/잔여/의사결정 항목을 요약 갱신한다.
