# Env Overrides - Spec

## English
Behavior
--------
- Read env vars and override config values.
- Convert types (int/float/bool) when needed.
 - If conversion fails, value is used as string (no warning).

Config
------
- AI_EVENTS_POST_URL
- AI_INGEST_FPS_LIMIT
- AI_EVENTS_SNAPSHOT_BASE_DIR
- AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX
- AI_LOGGING_LEVEL
- AI_LOGGING_FORMAT
- AI_MODEL_MODE

Edge Cases
----------
- Invalid type -> use string value (no warning).

Status
------
Implemented in `src/ai/config.py`.

Code Mapping
------------
- Env overrides: `src/ai/config.py` (`apply_env_overrides`)

## 한국어
동작
----
- 환경 변수를 읽어 설정 값을 오버라이드한다.
- 필요 시 타입(int/float/bool) 변환을 수행한다.
- 변환 실패 시 문자열로 사용하며 경고 로그는 없다.

설정
----
- AI_EVENTS_POST_URL
- AI_INGEST_FPS_LIMIT
- AI_EVENTS_SNAPSHOT_BASE_DIR
- AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX
- AI_LOGGING_LEVEL
- AI_LOGGING_FORMAT
- AI_MODEL_MODE

엣지 케이스
----------
- 타입이 잘못되면 문자열로 사용한다.

상태
----
`src/ai/config.py`에 구현됨.

코드 매핑
---------
- 환경변수 오버라이드: `src/ai/config.py` (`apply_env_overrides`)
