# Snapshot Public Path - Spec

## English
Behavior
--------
- Given base_dir and public_prefix, map to public URL.
- Preserve relative directory layout.

Config
------
- events.snapshot.public_prefix

Edge Cases
----------
- If public_prefix is empty, return original path.

Status
------
Implemented in `src/ai/events/snapshot.py`.

Code Mapping
------------
- Public path mapping: `src/ai/events/snapshot.py` (`to_public_path`)

## 한국어
동작
----
- base_dir와 public_prefix를 이용해 공개 URL로 매핑한다.
- 상대 디렉터리 구조를 유지한다.

설정
----
- events.snapshot.public_prefix

엣지 케이스
----------
- public_prefix가 비어 있으면 원본 경로를 반환한다.

상태
----
`src/ai/events/snapshot.py`에 구현됨.

코드 매핑
---------
- 공개 경로 매핑: `src/ai/events/snapshot.py` (`to_public_path`)
