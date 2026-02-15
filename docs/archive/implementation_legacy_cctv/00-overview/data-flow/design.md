# Data Flow - Design

## English
Purpose
-------
- Describe how data moves through the pipeline end-to-end.

Key Decisions
-------------
- Keep flow linear: Source -> Sampler -> Builder -> Emitter.
- Avoid side effects in the middle stages.

Interfaces
----------
- Inputs:
  - Frame stream
- Outputs:
  - Event stream

Notes
-----
- Snapshot writing is a side path from EventBuilder.

Code Mapping
------------
- Flow wiring: `src/ai/pipeline/core.py`
- Builders/emitters: `src/ai/pipeline/events.py`, `src/ai/pipeline/emitter.py`

## 한국어
목적
-----
- 파이프라인의 end-to-end 데이터 흐름을 설명한다.

핵심 결정
---------
- 흐름을 선형으로 유지: Source -> Sampler -> Builder -> Emitter.
- 중간 단계에서 부수 효과를 피한다.

인터페이스
----------
- 입력:
  - 프레임 스트림
- 출력:
  - 이벤트 스트림

노트
-----
- 스냅샷 저장은 EventBuilder에서 분기되는 사이드 경로이다.

코드 매핑
---------
- 흐름 연결: `src/ai/pipeline/core.py`
- 빌더/에미터: `src/ai/pipeline/events.py`, `src/ai/pipeline/emitter.py`
