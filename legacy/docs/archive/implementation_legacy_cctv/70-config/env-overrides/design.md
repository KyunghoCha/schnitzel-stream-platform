# Env Overrides - Design

## English
Purpose
-------
- Allow configuration via environment variables.

Key Decisions
-------------
- Support prefix `AI_` for overrides.
- Environment overrides take precedence over YAML.

Interfaces
----------
- Inputs:
  - environment variables
- Outputs:
  - merged config

Notes
-----
- Keep mapping table in config loader.

Code Mapping
------------
- Env overrides: `src/ai/config.py` (`apply_env_overrides`)

## 한국어
목적
-----
- 환경 변수로 설정을 오버라이드할 수 있게 한다.

핵심 결정
---------
- `AI_` 접두사로 오버라이드를 지원한다.
- 환경 변수는 YAML보다 우선한다.

인터페이스
----------
- 입력:
  - 환경 변수
- 출력:
  - 병합된 설정

노트
-----
- 매핑 테이블은 config loader에 유지한다.

코드 매핑
---------
- 환경변수 오버라이드: `src/ai/config.py` (`apply_env_overrides`)
