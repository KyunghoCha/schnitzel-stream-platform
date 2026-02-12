# Snapshot Writer - Spec

## English
Behavior
--------
- Encode frame to JPEG and write to base_dir.
- Return snapshot_path on success, None on failure.

Config
------
- events.snapshot.base_dir
- events.snapshot.public_prefix

Edge Cases
----------
- If write fails, log and continue (no crash).

Status
------
Implemented in `src/ai/events/snapshot.py`.

Code Mapping
------------
- Snapshot save: `src/ai/events/snapshot.py` (`save_snapshot`)

## 한국어
동작
----
- 프레임을 JPEG로 인코딩하여 base_dir에 기록한다.
- 성공 시 snapshot_path, 실패 시 None 반환.

설정
----
- events.snapshot.base_dir
- events.snapshot.public_prefix

엣지 케이스
----------
- 쓰기 실패 시 로그만 남기고 계속 진행한다(크래시 없음).

상태
----
`src/ai/events/snapshot.py`에 구현됨.

코드 매핑
---------
- 스냅샷 저장: `src/ai/events/snapshot.py` (`save_snapshot`)
