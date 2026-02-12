# Logging - Spec

## English
Behavior
--------
- Log to stdout and file.
- Rotate files based on size and backup count.
- Include camera_id in log filename to prevent collisions across processes.

Config
------
- AI_LOG_LEVEL
- AI_LOG_FORMAT
- AI_LOG_MAX_BYTES
- AI_LOG_BACKUP_COUNT

Edge Cases
----------
- If log directory is missing, create it.

Status
------
Implemented in `src/ai/logging_setup.py`.

Code Mapping
------------
- Logging setup/formatters: `src/ai/logging_setup.py`

## 한국어
동작
----
- stdout과 파일에 로그를 기록한다.
- 크기와 백업 개수 기준으로 파일을 회전한다.
- 프로세스 충돌을 막기 위해 로그 파일명에 camera_id를 포함한다.

설정
----
- AI_LOG_LEVEL
- AI_LOG_FORMAT
- AI_LOG_MAX_BYTES
- AI_LOG_BACKUP_COUNT

엣지 케이스
----------
- 로그 디렉터리가 없으면 생성한다.

상태
----
`src/ai/logging_setup.py`에 구현됨.

코드 매핑
---------
- 로깅 설정/포맷터: `src/ai/logging_setup.py`
