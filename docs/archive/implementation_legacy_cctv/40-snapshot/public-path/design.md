# Snapshot Public Path - Design

## English
Purpose
-------
- Map filesystem snapshot paths to public URLs.

Key Decisions
-------------
- Use public_prefix from config.
- Map base_dir path to public_prefix (preserve relative layout).

Interfaces
----------
- Inputs:
  - base_dir
  - public_prefix
  - file_path
- Outputs:
  - public_path

Notes
-----
- Backend must serve the public_prefix path.

Code Mapping
------------
- Public path mapping: `src/ai/events/snapshot.py` (`to_public_path`)

## 한국어
목적
-----
- 파일 시스템 스냅샷 경로를 공개 URL로 매핑한다.

핵심 결정
---------
- 설정의 public_prefix를 사용한다.
- base_dir 경로를 public_prefix로 치환하여 상대 레이아웃을 유지한다.

인터페이스
----------
- 입력:
  - base_dir
  - public_prefix
  - file_path
- 출력:
  - public_path

노트
-----
- 백엔드는 public_prefix 경로를 서빙해야 한다.

코드 매핑
---------
- 공개 경로 매핑: `src/ai/events/snapshot.py` (`to_public_path`)
