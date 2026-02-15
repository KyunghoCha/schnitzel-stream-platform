# Cooldown Store - Design

## English
Purpose
-------
- Persist cooldown state per dedup key.

Key Decisions
-------------
- In-memory store with TTL pruning.
- Keyed by (camera_id, track_id, event_type) unless overridden.

Interfaces
----------
- Inputs:
  - dedup key
  - cooldown_sec
- Outputs:
  - allow/deny emit

Notes
-----
- Prune periodically to bound memory.

Code Mapping
------------
- Cooldown store: `src/ai/rules/dedup.py` (`CooldownStore`)

## 한국어
목적
-----
- 중복 억제를 위한 쿨다운 상태를 키별로 저장한다.

핵심 결정
---------
- TTL 기반으로 정리되는 인메모리 스토어.
- 기본 키는 (camera_id, track_id, event_type)이며 필요 시 오버라이드.

인터페이스
----------
- 입력:
  - dedup 키
  - cooldown_sec
- 출력:
  - emit 허용/차단

노트
-----
- 메모리 상한을 위해 주기적으로 prune한다.

코드 매핑
---------
- 쿨다운 스토어: `src/ai/rules/dedup.py` (`CooldownStore`)
