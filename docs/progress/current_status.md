# Current Status

Last updated: 2026-02-19

## English

- Runtime baseline: v2 node graph only
- Legacy runtime: removed from `main` (`P4.5` complete)
- Execution SSOT current step id: `P26.8` (productization closure completed)
- P10 hardening track (`P10.1`~`P10.5`) completed
- P11 demo track (`P11.1`~`P11.6`) completed
- P12 foundation track completed (`P12.1`~`P12.7`: validator-first process graph scope)
- P13 execution completion track completed (`P13.1`~`P13.8`: E1~E6 implementation-only lane done)
- P14 universal UX/TUI transition track completed (`P14.1`~`P14.5`)
- P15 UX preset onboarding track completed (`P15.1`~`P15.3`: preset launcher + profile-aware env checks + docs sync)
- P16 UX console and governance minimum baseline track completed (`P16.1`~`P16.5`: ops service layer + control API + audit/policy + web console + docs/CI sync)
- P17 governance hardening + UX consistency track completed (`P17.1`~`P17.6`: mutating auth hardening + audit rotation + policy drift gate + UX semantics + docs sync)
- P18 onboarding UX + one-command local console bootstrap track completed (`P18.1`~`P18.8`: stream_console + console env profile + lockfile CI + docs sync)
- P19 usability closure track completed (`P19.1`~`P19.8`: stream_run doctor + YOLO override flags + view/headless preset split + API/UI/docs/test sync)
- P20 graph authoring UX track completed (`P20.1`~`P20.8`: non-interactive graph wizard + template profiles + CI/docs/test sync)
- P21 dependency-first track completed (`P21.0`~`P21.8`: dependency baseline + bootstrap/env doctor alignment + graph editor ops/API/UI + CI/docs sync)
- P22 onboarding closure track completed (`P22.1`~`P22.8`: bootstrap contract hardening + setup parity + doctor/console guidance + onboarding CI/docs sync)
- P23 block editor hardening baseline completed (`P23.1`~`P23.8`: direct manipulation + kind visuals + built-in layout + readability + docs/tests sync)
- P23.9 interaction hotfix completed (drag smoothness + snap connect + overlap-safe align)
- P24 reliability hardening track completed (`P24.1`~`P24.7`: durable boundaries + restart/backlog/ack regressions + reliability smoke CI gate)
- P25 plugin DX closure track completed (`P25.1`~`P25.6`: scaffold dry-run/validate flow + contract checker + required CI + docs sync)
- P26 productization closure track completed (`P26.1`~`P26.8`: Lab RC semver freeze, command/SSOT drift gates, conda required lane, release-readiness aggregator, docs sync)
- Non-research completion rule satisfied: `P22`~`P26` done in order (research gates `R*`/`G*` remain out-of-scope)
- Owner split and research-gate contract: `docs/roadmap/owner_split_playbook.md` (`E*`/`R*`/`G*`)

For detailed status, always refer to:
- `docs/roadmap/execution_roadmap.md`
- `docs/roadmap/owner_split_playbook.md`

## 한국어

- 런타임 기준선: v2 노드 그래프 전용
- 레거시 런타임: `main`에서 제거 완료 (`P4.5` 완료)
- 실행 SSOT current step id: `P26.8` (제품화 마감 페이즈 완료)
- P10 하드닝 트랙(`P10.1`~`P10.5`) 완료
- P11 데모 트랙(`P11.1`~`P11.6`) 완료
- P12 foundation 트랙 완료(`P12.1`~`P12.7`: validator-first 프로세스 그래프 범위)
- P13 실행 완결 트랙 완료(`P13.1`~`P13.8`: 연구 제외 E1~E6 구현 레인 완료)
- P14 범용 UX/TUI 전환 트랙 완료(`P14.1`~`P14.5`)
- P15 UX 프리셋 온보딩 트랙 완료(`P15.1`~`P15.3`: 프리셋 실행기 + 프로필 기반 env 진단 + 문서 동기화)
- P16 UX 콘솔 + 거버넌스 최소선 트랙 완료(`P16.1`~`P16.5`: 공통 ops 서비스 + Control API + Audit/Policy + 웹 콘솔 + 문서/CI 동기화)
- P17 거버넌스 하드닝 + UX 정합성 트랙 완료(`P17.1`~`P17.6`: mutating 인증 강화 + 감사 회전 + 정책 드리프트 게이트 + UX 의미 명확화 + 문서 동기화)
- P18 온보딩 UX + 원커맨드 로컬 콘솔 부트스트랩 트랙 완료(`P18.1`~`P18.8`: stream_console + console env 프로필 + lockfile CI + 문서 동기화)
- P19 사용성 마감 트랙 완료(`P19.1`~`P19.8`: stream_run doctor + YOLO override 옵션 + view/headless 프리셋 분리 + API/UI/문서/테스트 동기화)
- P20 그래프 작성 UX 트랙 완료(`P20.1`~`P20.8`: 비상호작용 graph wizard + 템플릿 프로필 + CI/문서/테스트 동기화)
- P21 의존성 우선 트랙 완료(`P21.0`~`P21.8`: 의존성 기준선 + bootstrap/env doctor 정렬 + 그래프 편집 ops/API/UI + CI/문서 동기화)
- P22 온보딩 완결 트랙 완료(`P22.1`~`P22.8`: bootstrap 계약 하드닝 + setup 동급 정렬 + doctor/console 가이드 + 온보딩 CI/문서 동기화)
- P23 블록 편집기 하드닝 기준선 완료(`P23.1`~`P23.8`: 직접 조작 + kind 시각화 + 내장 정렬 + 결과 가독성 + 문서/테스트 동기화)
- P23.9 상호작용 핫픽스 완료(드래그 반응 개선 + 스냅 연결 + 정렬 겹침 방지)
- P24 운영 신뢰성 하드닝 트랙 완료(`P24.1`~`P24.7`: durable 경계/재시작 회귀/신뢰성 스모크 CI 게이트 반영)
- P25 플러그인 DX 마감 트랙 완료(`P25.1`~`P25.6`: 스캐폴드 dry-run/validate + 계약검사기 + required CI + 문서 동기화)
- P26 제품화 마감 트랙 완료(`P26.1`~`P26.8`: Lab RC semver 동결, 명령면/SSOT 드리프트 게이트, conda required 레인, 릴리즈 집약 명령, 문서 동기화)
- 연구 제외 완성 기준 충족: `P22`~`P26` 순차 완료(`R*`/`G*`는 비범위 유지)
- 소유권 분리/연구 게이트 계약: `docs/roadmap/owner_split_playbook.md` (`E*`/`R*`/`G*`)

상세 상태는 아래를 기준으로 본다:
- `docs/roadmap/execution_roadmap.md`
- `docs/roadmap/owner_split_playbook.md`
