# Runtime Profiles - Spec

## English
Behavior
--------
- Load `configs/*.yaml` first.
- Apply env overrides.
- If `app.env` is set (`dev|prod`), merge `{env}.yaml` last.

Config
------
- app.env (dev|prod)
- templates: `configs/dev.yaml`, `configs/prod.yaml`

Edge Cases
----------
- Unknown profile -> fallback to default.

Status
------
Implemented in `src/ai/pipeline/config.py`.

Code Mapping
------------
- Profile merge: `src/ai/pipeline/config.py`

## 한국어
동작
----
- `configs/*.yaml`을 먼저 로드한다.
- 환경 변수 오버라이드를 적용한다.
- `app.env`가 (`dev|prod`)이면 `{env}.yaml`을 마지막에 병합한다.

설정
----
- app.env (dev|prod)
- 템플릿: `configs/dev.yaml`, `configs/prod.yaml`

엣지 케이스
----------
- 알 수 없는 프로파일이면 default로 폴백.

상태
----
`src/ai/pipeline/config.py`에 구현됨.

코드 매핑
---------
- 프로파일 병합: `src/ai/pipeline/config.py`
