# Zone Evaluation - Design

## English
Purpose
-------
- Decide whether an event is inside any configured zone.

Key Decisions
-------------
- Evaluate zones in order; first match returns.
- Only enabled zones are considered.

Interfaces
----------
- Inputs:
  - event_type
  - bbox
  - zones list
- Outputs:
  - zone result {zone_id, inside}

Notes
-----
- If no zones, return inside=false with zone_id="".

Verification
------------
- Use a small polygon and bbox to confirm inside/outside.

Code Mapping
------------
- Zone evaluator: `src/ai/rules/zones.py` (`evaluate_zones`, `ZoneEvaluator`)

## 한국어
목적
-----
- 이벤트가 설정된 zone 내부인지 여부를 판단한다.

핵심 결정
---------
- zone을 순서대로 평가하며, 첫 매칭이 반환된다.
- 활성화된 zone만 고려한다.

인터페이스
----------
- 입력:
  - event_type
  - bbox
  - zones 목록
- 출력:
  - zone 결과 {zone_id, inside}

노트
-----
- zone이 없으면 inside=false, zone_id=""을 반환한다.

검증
----
- 작은 폴리곤과 bbox로 inside/outside를 확인한다.

코드 매핑
---------
- zone 평가: `src/ai/rules/zones.py` (`evaluate_zones`, `ZoneEvaluator`)
