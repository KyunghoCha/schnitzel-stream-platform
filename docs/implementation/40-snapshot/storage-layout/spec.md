# Snapshot Storage Layout - Spec

## English
Behavior
--------
- Build relative path using `{site_id}/{camera_id}/{timestamp}_{track_id}.jpg`.
- Timestamp is sanitized for filename safety.
- Ensure directories exist before write.

Edge Cases
----------
- track_id missing -> omit from filename.

Status
------
Implemented in `src/ai/events/snapshot.py`.

Code Mapping
------------
- Path builder: `src/ai/events/snapshot.py` (`build_snapshot_path`)

## 한국어
동작
----
- `{site_id}/{camera_id}/{timestamp}_{track_id}.jpg` 형식으로 경로를 구성한다.
- 타임스탬프는 파일명 안전성을 위해 정규화된다.
- 쓰기 전에 디렉터리 존재를 보장한다.

엣지 케이스
----------
- track_id가 없으면 파일명에서 생략한다.

상태
----
`src/ai/events/snapshot.py`에 구현됨.

코드 매핑
---------
- 경로 생성: `src/ai/events/snapshot.py` (`build_snapshot_path`)
