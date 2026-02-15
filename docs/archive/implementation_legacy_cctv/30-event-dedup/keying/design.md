# Dedup Keying - Design

## English
Purpose
-------
- Define how dedup keys are composed.

Key Decisions
-------------
- Use (camera_id, track_id, event_type) by default.
- Allow override for events without track_id.

Interfaces
----------
- Inputs:
  - event payload
- Outputs:
  - dedup key

Notes
-----
- Current payload does not include roi_id; use track_id when available, else fallback key.

Code Mapping
------------
- Key builder: `src/ai/rules/dedup.py` (`build_dedup_key`)

## 한국어
목적
-----
- 중복 억제 키 구성 방식을 정의한다.

핵심 결정
---------
- 기본 키는 (camera_id, track_id, event_type).
- track_id가 없는 이벤트는 오버라이드를 허용한다.

인터페이스
----------
- 입력:
  - 이벤트 페이로드
- 출력:
  - dedup 키

노트
----
- 현재 페이로드에 roi_id가 없으므로 track_id 우선, 없으면 fallback 키를 사용한다.

코드 매핑
---------
- 키 생성: `src/ai/rules/dedup.py` (`build_dedup_key`)
