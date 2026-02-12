# Rule Point - Spec

## English
Behavior
--------
- If event_type is mapped, use the mapped rule point.
- Else use default (bottom_center).

Config
------
- rules.rule_point_by_event_type

Edge Cases
----------
- Invalid bbox -> return None and skip zone evaluation.

Status
------
Implemented in `src/ai/rules/zones.py`.

Code Mapping
------------
- Rule point mapping: `src/ai/rules/zones.py` (`rule_point_from_bbox`)

## 한국어
동작
----
- event_type에 매핑이 있으면 해당 rule point를 사용한다.
- 없으면 기본값(bottom_center)을 사용한다.

설정
----
- rules.rule_point_by_event_type

엣지 케이스
----------
- bbox가 유효하지 않으면 None을 반환하고 zone 평가를 스킵한다.

상태
----
`src/ai/rules/zones.py`에 구현됨.

코드 매핑
---------
- 룰 포인트 매핑: `src/ai/rules/zones.py` (`rule_point_from_bbox`)
