# Snapshot Writer - Design

## English
Purpose
-------
- Save event snapshots to disk with a deterministic path.

Key Decisions
-------------
- Build path from site_id, camera_id, timestamp, track_id.
- Use JPEG encoding via OpenCV.

Interfaces
----------
- Inputs:
  - frame
  - event metadata
  - base_dir
- Outputs:
  - snapshot_path

Notes
-----
- Create directories if missing.

Code Mapping
------------
- Snapshot save: `src/ai/events/snapshot.py` (`save_snapshot`)

## 한국어
목적
-----
- 이벤트 스냅샷을 디스크에 결정적인 경로로 저장한다.

핵심 결정
---------
- site_id, camera_id, timestamp, track_id로 경로를 구성한다.
- OpenCV로 JPEG 인코딩한다.

인터페이스
----------
- 입력:
  - frame
  - 이벤트 메타데이터
  - base_dir
- 출력:
  - snapshot_path

노트
-----
- 디렉터리가 없으면 생성한다.

코드 매핑
---------
- 스냅샷 저장: `src/ai/events/snapshot.py` (`save_snapshot`)
