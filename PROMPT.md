# Handoff Prompt (schnitzel-stream-platform)

Last updated: 2026-02-16

Current step id (SSOT): `P16.1` (see `docs/roadmap/execution_roadmap.md`)

## English

This file is the stable handoff entrypoint.

Canonical sources:
- `PROMPT_CORE.md` (working rules + execution context)
- `docs/roadmap/execution_roadmap.md` (execution SSOT)
- `docs/index.md` (active docs entrypoint)

Current baseline:
- runtime entrypoint: `python -m schnitzel_stream`
- graph format: v2 node graph (`version: 2`)
- legacy runtime/docs removed from working tree
- historical legacy references are available in git tag: `pre-legacy-purge-20260216`
- hardening track completed (`P10.1` -> `P10.5`)
- demo packaging track completed (`P11.1` -> `P11.6`)
- process-graph foundation track completed (`P12.1`~`P12.7`, validator-first with SQLite bridge)
- execution completion track completed (`P13.1`~`P13.8`, implementation-only E1~E6 lane)
- universal UX/TUI transition track completed (`P14.1`~`P14.5`)
- UX preset onboarding track completed (`P15.1`~`P15.3`, presets + env profiles + docs sync)
- UX console and governance minimum baseline track started (`P16.1`, shared ops service layer)

Verification (local):
- syntax check: `python3 -m compileall -q src tests`
- tests: `pip install -r requirements-dev.txt` then `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`

---

## 한국어

이 파일은 핸드오프용 진입 문서다.

기준 문서:
- `PROMPT_CORE.md` (작업 규칙 + 실행 컨텍스트)
- `docs/roadmap/execution_roadmap.md` (실행 SSOT)
- `docs/index.md` (active 문서 진입점)

현재 기준선:
- 런타임 엔트리포인트: `python -m schnitzel_stream`
- 그래프 포맷: v2 노드 그래프(`version: 2`)
- 레거시 런타임/문서는 워킹 트리에서 제거됨
- 과거 레거시 이력은 git 태그 `pre-legacy-purge-20260216`에서 조회
- 하드닝 트랙 완료(`P10.1` -> `P10.5`)
- 데모 패키징 트랙 완료(`P11.1` -> `P11.6`)
- 프로세스 그래프 foundation 트랙 완료(`P12.1`~`P12.7`, SQLite 기반 validator-first)
- 실행 완결 트랙 완료(`P13.1`~`P13.8`, 연구 제외 E1~E6 구현 레인)
- 범용 UX/TUI 전환 트랙 완료(`P14.1`~`P14.5`)
- UX 프리셋 온보딩 트랙 완료(`P15.1`~`P15.3`, 프리셋 + env 프로필 + 문서 동기화)
- UX 콘솔 + 거버넌스 최소선 트랙 시작(`P16.1`, 공통 ops 서비스 레이어)

검증(로컬):
- 문법 검사: `python3 -m compileall -q src tests`
- 테스트: `pip install -r requirements-dev.txt` 후 `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
