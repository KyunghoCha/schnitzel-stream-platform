# Rule Point - Design

## English
Purpose
-------
- Decide which point of a bbox is used for zone evaluation.

Key Decisions
-------------
- Use mapping by event_type (config-driven).
- Default to bbox bottom-center for intrusion.

Interfaces
----------
- Inputs:
  - bbox
  - event_type
- Outputs:
  - rule point (x, y)

Notes
-----
- Keep rule points configurable to support different use cases.

Code Mapping
------------
- Rule point mapping: `src/ai/rules/zones.py` (`rule_point_from_bbox`)

## 한국어
목적
-----
- zone 평가에 사용할 bbox 포인트를 결정한다.

핵심 결정
---------
- event_type별 매핑을 설정으로 제어한다.
- 침입 이벤트의 기본값은 bbox 하단 중앙.

인터페이스
----------
- 입력:
  - bbox
  - event_type
- 출력:
  - rule point (x, y)

노트
-----
- 다양한 케이스를 위해 rule point는 설정 가능해야 한다.

코드 매핑
---------
- 룰 포인트 매핑: `src/ai/rules/zones.py` (`rule_point_from_bbox`)
