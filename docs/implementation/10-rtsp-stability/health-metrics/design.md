# RTSP Health Metrics - Design

## English
Purpose
-------
- Track RTSP health (fps, drops, errors) for debugging and monitoring.

Key Decisions
-------------
- Maintain rolling stats in `MetricsTracker`.
- Emit metrics on a fixed interval.

Interfaces
----------
- Inputs:
  - frame counts
  - drop counts
  - error counts
- Outputs:
  - metrics payload log

Notes
-----
- Metrics should not block the frame loop.

Code Mapping
------------
- Metrics tracker: `src/ai/utils/metrics.py`
- Metrics logging: `src/ai/pipeline/core.py`

## 한국어
목적
-----
- RTSP 상태(fps, 드랍, 에러)를 추적하여 디버깅/모니터링에 사용한다.

핵심 결정
---------
- `MetricsTracker`에서 롤링 통계를 유지한다.
- 고정 주기로 메트릭을 발행한다.

인터페이스
----------
- 입력:
  - 프레임 카운트
  - 드랍 카운트
  - 에러 카운트
- 출력:
  - 메트릭 페이로드 로그

노트
-----
- 메트릭은 프레임 루프를 블로킹하지 않아야 한다.

코드 매핑
---------
- 메트릭 추적기: `src/ai/utils/metrics.py`
- 메트릭 로깅: `src/ai/pipeline/core.py`
