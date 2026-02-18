# Handoff Prompt (schnitzel-stream-platform)

Last updated: 2026-02-18

Current step id (SSOT): `P24.7` (see `docs/roadmap/execution_roadmap.md`)

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
- UX console and governance minimum baseline track completed (`P16.1`~`P16.5`, ops service layer + control API + governance minimum + web console + docs sync)
- governance hardening + UX consistency track completed (`P17.1`~`P17.6`, mutating auth hardening + audit retention rotation + policy drift gate + UX semantics sync)
- onboarding UX + one-command local console bootstrap track completed (`P18.1`~`P18.8`, stream_console + console env profile + lockfile CI + docs sync)
- usability closure no-env-first track completed (`P19.1`~`P19.8`, stream_run doctor + YOLO override flags + view/headless preset split + API/UI/docs/test sync)
- graph authoring UX track completed (`P20.1`~`P20.8`, CLI wizard template-profile lane + CI/docs/tests sync)
- dependency baseline + block editor MVP track completed (`P21.0`~`P21.8`, dependency-first execution lane)
- onboarding closure track completed (`P22.1`~`P22.8`, explicit 3-step onboarding closure + Win/Linux parity gates)
- block editor hardening baseline completed (`P23.1`~`P23.8`, direct manipulation UX hardening finished)
- P23.9 interaction hotfix completed (drag smoothness + snap connect + overlap-safe align)
- reliability hardening phase completed (`P24.1`~`P24.7`, durable-first reliability expansion delivered)

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
- UX 콘솔 + 거버넌스 최소선 트랙 완료(`P16.1`~`P16.5`, 공통 ops 서비스 + control API + 거버넌스 최소선 + 웹 콘솔 + 문서 동기화)
- 거버넌스 하드닝 + UX 정합성 트랙 완료(`P17.1`~`P17.6`, mutating 인증 강화 + 감사 보존 회전 + 정책 드리프트 게이트 + UX 의미 정합화)
- 온보딩 UX + 원커맨드 로컬 콘솔 부트스트랩 트랙 완료(`P18.1`~`P18.8`, stream_console + console env 프로필 + lockfile CI + 문서 동기화)
- 사용성 마감 무환경변수 우선 트랙 완료(`P19.1`~`P19.8`, stream_run doctor + YOLO override 옵션 + view/headless 프리셋 분리 + API/UI/문서/테스트 동기화)
- 그래프 작성 UX 트랙 완료(`P20.1`~`P20.8`, CLI wizard 템플릿 프로필 레인 + CI/문서/테스트 동기화)
- 의존성 기준선 + 블록 편집기 MVP 트랙 완료(`P21.0`~`P21.8`, dependency-first 실행 레인)
- 온보딩 완결 트랙 완료(`P22.1`~`P22.8`, 명시 3단계 온보딩 완결 + Win/Linux 동급 게이트)
- 블록 편집기 하드닝 기준선 완료(`P23.1`~`P23.8`, 직접 조작 UX 하드닝 완료)
- P23.9 상호작용 핫픽스 완료(드래그 반응 개선 + 스냅 연결 + 정렬 겹침 방지)
- 운영 신뢰성 하드닝 페이즈 완료(`P24.1`~`P24.7`, durable-first 신뢰성 확장 반영 완료)

검증(로컬):
- 문법 검사: `python3 -m compileall -q src tests`
- 테스트: `pip install -r requirements-dev.txt` 후 `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
