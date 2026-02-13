# Entrypoint - Design

## English

Purpose
-------

- Define container startup behavior.

Key Decisions
-------------

- Entry uses `python -m schnitzel_stream` (Dockerfile CMD default).
- Dry-run is opt-in via CLI `--dry-run`.
- Allow config via env variables.

Interfaces
----------

- Inputs:
  - env vars
- Outputs:
  - pipeline process

Notes
-----

- Keep entrypoint minimal.

Code Mapping
------------

- Docker CMD: `Dockerfile`
- Optional script: (Removed in favor of direct python invocation)

## 한국어

목적
-----

- 컨테이너 시작 동작을 정의한다.

핵심 결정
---------

- `python -m schnitzel_stream`로 시작한다(Dockerfile 기본 CMD).
- 드라이런은 `--dry-run`을 명시적으로 전달해 사용한다.
- 환경 변수로 설정을 전달한다.

인터페이스
----------

- 입력:
  - 환경 변수
- 출력:
  - 파이프라인 프로세스

노트
-----

- entrypoint는 최소한으로 유지한다.

코드 매핑
---------

- Docker CMD: `Dockerfile`
- 선택 스크립트: (직접 Python 실행으로 대체됨)
