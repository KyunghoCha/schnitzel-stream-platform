# Runtime Profiles - Design

## English
Purpose
-------
- Provide dev/prod profile defaults.

Key Decisions
-------------
- Merge `configs/*.yaml` first, then env overrides, then profile file.

Interfaces
----------
- Inputs:
  - profile name
- Outputs:
  - merged config

Notes
-----
- Keep profiles minimal.
- Templates: `configs/dev.yaml`, `configs/prod.yaml`.

Code Mapping
------------
- Profile merge: `src/ai/pipeline/config.py`

## 한국어
목적
-----
- dev/prod 프로파일 기본값을 제공한다.

핵심 결정
---------
- 프로파일로 로깅/메트릭을 조정한다.
- 환경 변수 오버라이드를 먼저 적용한 뒤 프로파일을 병합한다.

인터페이스
----------
- 입력:
  - 프로파일 이름
- 출력:
  - 병합된 설정

노트
-----
- 프로파일은 최소한으로 유지한다.
- 템플릿: `configs/dev.yaml`, `configs/prod.yaml`.

코드 매핑
---------
- 프로파일 병합: `src/ai/pipeline/config.py`
