# Zone Source - Design

## English
Purpose
-------
- Support loading zones from file or backend API.

Key Decisions
-------------
- Provide a loader interface with two implementations.
- Cache zones with TTL for API and file modes.

Interfaces
----------
- Inputs:
  - source type (file|api)
  - file path or api base_url
- Outputs:
  - zones list

Notes
-----
- API failures should fall back to cached zones.

Code Mapping
------------
- Zone loading/cache: `src/ai/rules/zones.py`

## 한국어
목적
-----
- 파일 또는 백엔드 API에서 zone을 로드할 수 있도록 한다.

핵심 결정
---------
- 두 가지 구현을 가진 로더 인터페이스를 제공한다.
- API/파일 모드 모두 TTL 캐시를 사용한다.

인터페이스
----------
- 입력:
  - source type (file|api)
  - file path 또는 api base_url
- 출력:
  - zones 목록

노트
-----
- API 실패 시 캐시된 zone으로 폴백해야 한다.

코드 매핑
---------
- zone 로딩/캐시: `src/ai/rules/zones.py`
