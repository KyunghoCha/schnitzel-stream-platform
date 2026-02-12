# Metrics - Design

## English
Purpose
-------
- Provide rolling metrics for fps, drops, and errors.

Key Decisions
-------------
- Maintain windowed FPS using a time window.
- Emit metrics periodically.

Interfaces
----------
- Inputs:
  - frame counts
  - error counts
- Outputs:
  - metrics payload

Notes
-----
- Use dedicated logger (`ai.metrics`).

Code Mapping
------------
- Metrics tracker: `src/ai/utils/metrics.py`

## 한국어
목적
-----
- fps, drop, error에 대한 롤링 메트릭을 제공한다.

핵심 결정
---------
- 시간 윈도우 기반 FPS를 유지한다.
- 주기적으로 메트릭을 발행한다.

인터페이스
----------
- 입력:
  - 프레임 카운트
  - 에러 카운트
- 출력:
  - 메트릭 페이로드

노트
-----
- 전용 로거(`ai.metrics`)를 사용한다.

코드 매핑
---------
- 메트릭 추적기: `src/ai/utils/metrics.py`
