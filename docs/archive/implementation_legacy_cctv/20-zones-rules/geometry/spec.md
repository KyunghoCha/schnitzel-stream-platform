# Geometry - Spec

## English
Behavior
--------
- Given point and polygon, return True if point is inside.
- Boundary points return True (inclusive).

Edge Cases
----------
- Degenerate polygons (less than 3 points) return False.

Status
------
Implemented in `src/ai/rules/zones.py`.

Code Mapping
------------
- Geometry: `src/ai/rules/zones.py` (`point_in_polygon`)

## 한국어
동작
----
- 점과 폴리곤이 주어지면 내부 여부를 반환한다.
- 경계점도 True로 처리한다(포함).

엣지 케이스
----------
- 점이 3개 미만인 폴리곤은 False 반환.

상태
----
`src/ai/rules/zones.py`에 구현됨.

코드 매핑
---------
- 기하: `src/ai/rules/zones.py` (`point_in_polygon`)
