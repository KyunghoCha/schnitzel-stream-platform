# Severity Override - Spec

## English
Behavior
--------
- If severity changes, emit even within cooldown.
- If severity stays the same, apply cooldown.

Config
------
- None (severity ordering not configurable yet)

Edge Cases
----------
- Any severity change triggers immediate emit (no ordering required).

Status
------
Implemented in `src/ai/rules/dedup.py`.

Code Mapping
------------
- Severity override: `src/ai/rules/dedup.py` (`CooldownStore.allow`)

## 한국어
동작
----
- severity가 달라지면 쿨다운 내라도 emit한다.
- severity가 동일하면 쿨다운을 적용한다.

설정
----
- 없음 (severity 순서 설정 미지원)

엣지 케이스
----------
- severity가 달라지면 즉시 emit한다(순서 비교 없음).

상태
----
`src/ai/rules/dedup.py`에 구현됨.

코드 매핑
---------
- severity 오버라이드: `src/ai/rules/dedup.py` (`CooldownStore.allow`)
