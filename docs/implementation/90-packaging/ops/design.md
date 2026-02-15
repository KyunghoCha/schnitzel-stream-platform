# Ops Packaging - Design

## English
Purpose
-------
- Define runtime packaging for ops usage.

Key Decisions
-------------
- Provide Docker-based runtime.
- Mount snapshots to host path.

Interfaces
----------
- Inputs:
  - volume paths
- Outputs:
  - running container

Notes
-----
- Logs should be accessible on host.

Code Mapping
------------
- Runbook: `docs/legacy/ops/ops_runbook.md`
- Dockerfile: `Dockerfile`

## 한국어
목적
-----
- 운영 환경에서 사용할 런타임 패키징을 정의한다.

핵심 결정
---------
- Docker 기반 런타임 제공.
- 스냅샷을 호스트 경로로 마운트.

인터페이스
----------
- 입력:
  - 볼륨 경로
- 출력:
  - 실행 중인 컨테이너

노트
-----
- 로그는 호스트에서 접근 가능해야 한다.

코드 매핑
---------
- 런북: `docs/legacy/ops/ops_runbook.md`
- Dockerfile: `Dockerfile`
