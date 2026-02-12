# Cooldown Store - Spec

## English
Behavior
--------
- On emit, record timestamp for key.
- If cooldown not elapsed, block emit.

Config
------
- dedup.cooldown_sec
- dedup.prune_interval

Edge Cases
----------
- If track_id missing, use fallback key (e.g., camera_id + event_type).

Status
------
Implemented in `src/ai/rules/dedup.py`.

Code Mapping
------------
- Cooldown store: `src/ai/rules/dedup.py` (`CooldownStore`)

## 한국어
동작
----
- emit 시 키에 대한 타임스탬프를 기록한다.
- 쿨다운이 지나지 않았으면 emit을 차단한다.

설정
----
- dedup.cooldown_sec
- dedup.prune_interval

엣지 케이스
----------
- track_id가 없으면 대체 키(예: camera_id + event_type)를 사용한다.

상태
----
`src/ai/rules/dedup.py`에 구현됨.

코드 매핑
---------
- 쿨다운 스토어: `src/ai/rules/dedup.py` (`CooldownStore`)
