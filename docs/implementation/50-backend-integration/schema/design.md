# Backend Event Schema - Design

## English
Purpose
-------
- Align event payload structure between AI and backend.

Key Decisions
-------------
- Use `docs/packs/vision/event_protocol_v0.2.md` as source of truth.
- Keep additional fields optional for extensibility.

Interfaces
----------
- Inputs:
  - event payload
- Outputs:
  - backend acceptance

Notes
-----
- Backward compatibility is required when adding fields.

Code Mapping
------------
- Event schema builder: `src/ai/events/schema.py`
- Payload validation point: `src/ai/clients/backend_api.py` (backend may reject)

## 한국어
목적
-----
- AI와 백엔드 간 이벤트 페이로드 구조를 정렬한다.

핵심 결정
---------
- `docs/packs/vision/event_protocol_v0.2.md`를 단일 기준으로 한다.
- 확장을 위해 추가 필드는 optional로 유지한다.

인터페이스
----------
- 입력:
  - 이벤트 페이로드
- 출력:
  - 백엔드 수락 여부

노트
-----
- 필드 추가 시 하위 호환이 필요하다.

코드 매핑
---------
- 이벤트 스키마 빌더: `src/ai/events/schema.py`
- 페이로드 검증 지점: `src/ai/clients/backend_api.py` (백엔드에서 거부 가능)
