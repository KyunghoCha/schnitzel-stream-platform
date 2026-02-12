# Snapshot Storage Layout - Design

## English
Purpose
-------
- Define deterministic folder layout for snapshots.

Key Decisions
-------------
- Layout: `{base}/{site_id}/{camera_id}/{timestamp}_{track_id}.jpg`
- Use timestamp string for uniqueness.

Interfaces
----------
- Inputs:
  - site_id
  - camera_id
  - timestamp
  - track_id
- Outputs:
  - relative path

Notes
-----
- Keep path stable for backend lookup.

Code Mapping
------------
- Path builder: `src/ai/events/snapshot.py` (`build_snapshot_path`)

## 한국어
목적
-----
- 스냅샷의 결정적 폴더 레이아웃을 정의한다.

핵심 결정
---------
- 레이아웃: `{base}/{site_id}/{camera_id}/{timestamp}_{track_id}.jpg`
- 고유성을 위해 타임스탬프 문자열을 사용한다.

인터페이스
----------
- 입력:
  - site_id
  - camera_id
  - timestamp
  - track_id
- 출력:
  - 상대 경로

노트
-----
- 백엔드 조회를 위해 경로를 안정적으로 유지한다.

코드 매핑
---------
- 경로 생성: `src/ai/events/snapshot.py` (`build_snapshot_path`)
