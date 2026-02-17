# Handoff Prompt Core (schnitzel-stream-platform)

Last updated: 2026-02-17

## English

You are working on the universal stream platform repository `schnitzel-stream-platform`.

Execution SSOT:
- `docs/roadmap/execution_roadmap.md`

Current status:
- Current step id: `P19.1` (usability closure no-env-first track kickoff)
- Core platform phases (`P0`~`P10`) are complete on `main`
- Demo packaging phase (`P11`) is complete on `main`
- Process-graph foundation phase (`P12`) is complete (`validator-first`, SQLite bridge)
- Execution completion phase (`P13`) is completed for implementation-only items (`E1`~`E6`)
- Universal UX/TUI transition phase (`P14`) is complete
- UX preset onboarding phase (`P15`) is complete (preset surface + profile-aware env checks)
- UX console and governance minimum baseline phase (`P16`) is complete
- Governance hardening and UX consistency phase (`P17`) is complete
- Onboarding UX and one-command local console bootstrap phase (`P18`) is complete
- Usability closure no-env-first phase (`P19`) is now open
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
- 현재 step id: `P19.1` (사용성 마감 무환경변수 우선 트랙 착수)
- 코어 플랫폼 단계(`P0`~`P10`)는 `main` 기준 완료
- 데모 패키징 단계(`P11`) 완료
- 프로세스 그래프 foundation 단계(`P12`) 완료(`validator-first`, SQLite 브리지)
- 실행 완결 단계(`P13`) 완료(`E1`~`E6`, 연구 제외 구현 레인)
- 범용 UX/TUI 전환 단계(`P14`) 완료
- UX 프리셋 온보딩 단계(`P15`) 완료(프리셋 실행기 + 프로필 기반 환경 진단)
- UX 콘솔 + 거버넌스 최소선 단계(`P16`) 완료
- 거버넌스 하드닝 + UX 정합성 단계(`P17`) 완료
- 온보딩 UX + 원커맨드 로컬 콘솔 부트스트랩 단계(`P18`) 완료
- 사용성 마감 무환경변수 우선 단계(`P19`) 착수
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
