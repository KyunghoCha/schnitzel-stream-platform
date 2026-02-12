# Zone Evaluation - Spec

## English
Behavior
--------
- Compute rule point from bbox (see rule-point spec).
- For each zone, check point-in-polygon.
- Return first match; else inside=false.

Config
------
- rules.rule_point_by_event_type
- zones.source (api|file|none; `none` disables zone evaluation)
- zones.api.cache_ttl_sec

Edge Cases
----------
- Empty zones list -> `zone_id=""`, `inside=false`
- Invalid polygon -> skip and log

Status
------
Implemented in `src/ai/rules/zones.py`.

Code Mapping
------------
- Zone evaluation: `src/ai/rules/zones.py` (`evaluate_zones`, `ZoneEvaluator`)

## 한국어
동작
----
- bbox에서 rule point를 계산한다(룰-포인트 명세 참조).
- 각 zone에 대해 point-in-polygon을 검사한다.
- 첫 매칭을 반환하고, 없으면 inside=false.

설정
----
- rules.rule_point_by_event_type
- zones.source (api|file|none; `none`이면 zone 평가 비활성)
- zones.api.cache_ttl_sec

엣지 케이스
----------
- zones 목록이 비어 있으면 `zone_id=""`, `inside=false`
- 잘못된 폴리곤은 스킵하고 로그

상태
----
`src/ai/rules/zones.py`에 구현됨.

코드 매핑
---------
- zone 평가: `src/ai/rules/zones.py` (`evaluate_zones`, `ZoneEvaluator`)
