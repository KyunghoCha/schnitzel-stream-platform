# Logging - Design

## English
Purpose
-------
- Provide consistent logs for debugging and ops.

Key Decisions
-------------
- Support plain and JSON log formats.
- Include structured fields when available.
- Rotate log files by size.

Interfaces
----------
- Inputs:
  - log level
  - log format
- Outputs:
  - stdout + log file

Notes
-----
- Mask RTSP passwords and backend post_url credentials in logs.

Code Mapping
------------
- Logging setup/formatters: `src/ai/logging_setup.py`

## 한국어
목적
-----
- 디버깅/운영을 위한 일관된 로그를 제공한다.

핵심 결정
---------
- plain/JSON 로그 포맷을 지원한다.
- 가능한 경우 구조화 필드를 포함한다.
- 로그 파일은 크기 기준으로 회전한다.

인터페이스
----------
- 입력:
  - 로그 레벨
  - 로그 포맷
- 출력:
  - stdout + 로그 파일

노트
-----
- 로그에 RTSP 비밀번호와 backend post_url 자격 정보가 노출되지 않도록 마스킹한다.

코드 매핑
---------
- 로깅 설정/포맷터: `src/ai/logging_setup.py`
