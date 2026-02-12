# Conventions - Spec

## English
Behavior
--------
- Modules expose small, testable interfaces.
- Side effects limited to Source/Emitter.
- Shared utilities live under `src/ai/utils/` (e.g., URL masking).

Config
------
- All config lives in `configs/*.yaml` with overrides in CLI/env.

Edge Cases
----------
- If config is missing, defaults are used.

Status
------
Core conventions are implemented; event field naming rules are documented in `docs/contracts/protocol.md`.

Code Mapping
------------
- Config schema/loader: `src/ai/pipeline/config.py`
- Env override map: `src/ai/config.py`

## 한국어
동작
----
- 모듈은 작고 테스트 가능한 인터페이스를 제공한다.
- 부수 효과는 Source/Emitter로 제한한다.
- 공통 유틸은 `src/ai/utils/`에 둔다(예: URL 마스킹).

설정
----
- 모든 설정은 `configs/*.yaml`에 있으며 CLI/env로 오버라이드한다.

엣지 케이스
----------
- 설정이 없으면 기본값을 사용한다.

상태
----
핵심 컨벤션은 구현되었고, 이벤트 필드 네이밍 규칙은 `docs/contracts/protocol.md`에 문서화됨.

코드 매핑
---------
- 설정 스키마/로더: `src/ai/pipeline/config.py`
- 환경변수 오버라이드 맵: `src/ai/config.py`
