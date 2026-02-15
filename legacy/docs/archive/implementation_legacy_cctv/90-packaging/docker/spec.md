# Docker Packaging - Spec

## English
Behavior
--------
- Build image via `docker build`.
- Run container with volume for snapshots.

Config
------
- `/data/snapshots` mount recommended.

Edge Cases
----------
- Missing Dockerfile -> build fails.

Status
------
Dockerfile implemented in repo root.

Code Mapping
------------
- Dockerfile: `Dockerfile`

## 한국어
동작
----
- `docker build`로 이미지를 빌드한다.
- 스냅샷을 위한 볼륨을 마운트하여 컨테이너를 실행한다.

설정
----
- `/data/snapshots` 마운트를 권장.

엣지 케이스
----------
- Dockerfile이 없으면 빌드 실패.

상태
----
Dockerfile이 레포 루트에 구현됨.

코드 매핑
---------
- Dockerfile: `Dockerfile`
