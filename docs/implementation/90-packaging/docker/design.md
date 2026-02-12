# Docker Packaging - Design

## English
Purpose
-------
- Provide reproducible runtime environment.

Key Decisions
-------------
- Base image: python:3.11-slim
- Install minimal OS packages (libgl1, libglib2.0-0)
- Install Python deps via pip

Interfaces
----------
- Inputs:
  - source tree
- Outputs:
  - Docker image

Notes
-----
- Keep image small.

Code Mapping
------------
- Dockerfile: `Dockerfile`

## 한국어
목적
-----
- 재현 가능한 런타임 환경을 제공한다.

핵심 결정
---------
- 베이스 이미지: python:3.11-slim
- 최소 OS 패키지 설치(libgl1, libglib2.0-0)
- pip로 Python 의존성 설치

인터페이스
----------
- 입력:
  - 소스 트리
- 출력:
  - Docker 이미지

노트
-----
- 이미지 크기를 작게 유지한다.

코드 매핑
---------
- Dockerfile: `Dockerfile`
