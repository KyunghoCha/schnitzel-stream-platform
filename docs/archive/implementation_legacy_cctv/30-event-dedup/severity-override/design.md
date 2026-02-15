# Severity Override - Design

## English
Purpose
-------
- Re-emit events immediately when severity changes.

Key Decisions
-------------
- If severity changes (any direction), bypass cooldown.

Interfaces
----------
- Inputs:
  - current severity
  - last severity
- Outputs:
  - allow/deny emit

Notes
-----
- Severity ordering is not used; only equality/inequality is checked.

Code Mapping
------------
- Severity override: `src/ai/rules/dedup.py` (`CooldownStore.allow`)

## 한국어
목적
-----
- severity가 변경되면 즉시 재발행한다.

핵심 결정
---------
- severity가 바뀌면(상승/하락 관계없이) 쿨다운을 무시한다.

인터페이스
----------
- 입력:
  - 현재 severity
  - 이전 severity
- 출력:
  - emit 허용/차단

노트
-----
- severity 순서를 비교하지 않고 동일/변경 여부만 확인한다.

코드 매핑
---------
- severity 오버라이드: `src/ai/rules/dedup.py` (`CooldownStore.allow`)
