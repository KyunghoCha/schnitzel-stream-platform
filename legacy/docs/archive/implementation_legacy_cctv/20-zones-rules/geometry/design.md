# Geometry - Design

## English
Purpose
-------
- Provide point-in-polygon check for zone evaluation.

Key Decisions
-------------
- Use ray-casting algorithm (even-odd rule).
- Treat boundary as inside (inclusive).

Interfaces
----------
- Inputs:
  - point (x, y)
  - polygon list [[x,y],...]
- Outputs:
  - inside boolean

Notes
-----
- Polygon is assumed to be closed; last point need not repeat first.

Code Mapping
------------
- Geometry: `src/ai/rules/zones.py` (`point_in_polygon`)

## 한국어
목적
-----
- zone 평가를 위한 point-in-polygon 체크를 제공한다.

핵심 결정
---------
- 레이 캐스팅 알고리즘(짝/홀 규칙)을 사용한다.
- 경계는 내부로 간주한다(포함).

인터페이스
----------
- 입력:
  - point (x, y)
  - polygon 리스트 [[x,y],...]
- 출력:
  - inside 불리언

노트
-----
- 폴리곤은 닫혀 있다고 가정하며, 마지막 점이 첫 점을 반복할 필요는 없다.

코드 매핑
---------
- 기하: `src/ai/rules/zones.py` (`point_in_polygon`)
