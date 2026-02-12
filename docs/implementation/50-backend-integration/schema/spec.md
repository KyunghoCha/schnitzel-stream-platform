# Backend Event Schema - Spec

## English
Behavior
--------
- POST body must match required fields in `docs/contracts/protocol.md`.
- Unknown fields should be ignored by backend (forward compatibility).

Edge Cases
----------
- Missing required fields -> backend rejects.

Status
------
`docs/contracts/protocol.md` aligned; backend implementation pending.

Code Mapping
------------
- Event schema: `docs/contracts/protocol.md`
- Payload generation: `src/ai/events/schema.py`

## 한국어
동작
----
- POST 바디는 `docs/contracts/protocol.md`의 필수 필드를 충족해야 한다.
- 알 수 없는 필드는 백엔드에서 무시(전방 호환)해야 한다.

엣지 케이스
----------
- 필수 필드 누락 시 백엔드가 거부한다.

상태
----
`docs/contracts/protocol.md`는 정렬 완료, 백엔드 구현은 대기 중.

코드 매핑
---------
- 이벤트 스키마: `docs/contracts/protocol.md`
- 페이로드 생성: `src/ai/events/schema.py`
