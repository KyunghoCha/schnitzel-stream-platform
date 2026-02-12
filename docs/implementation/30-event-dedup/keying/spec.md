# Dedup Keying - Spec

## English
Behavior
--------
- Build key from event fields per policy.
- Use fallback when fields are missing.

Config
------
- None (fixed logic in code)

Edge Cases
----------
- Null track_id -> use camera_id + event_type.
- No ROI keying in current payload contract.

Status
------
Implemented in `src/ai/rules/dedup.py`.

Code Mapping
------------
- Key builder: `src/ai/rules/dedup.py` (`build_dedup_key`)

## 한국어
동작
----
- 정책에 따라 이벤트 필드로 키를 구성한다.
- 필드가 없으면 대체 키를 사용한다.

설정
----
- 없음 (코드에 고정 로직)

엣지 케이스
----------
- track_id가 null이면 camera_id + event_type 사용.
- ROI 기반 키잉은 현재 페이로드 계약에 없음.

상태
----
`src/ai/rules/dedup.py`에 구현됨.

코드 매핑
---------
- 키 생성: `src/ai/rules/dedup.py` (`build_dedup_key`)
