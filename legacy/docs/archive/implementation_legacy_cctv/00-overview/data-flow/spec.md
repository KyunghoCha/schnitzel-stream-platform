# Data Flow - Spec

## English
Behavior
--------
- Frames are read continuously from Source.
- Sampler decides which frames are processed.
- **Live sources** (`is_live=True`): `FrameProcessor` runs inference in a background worker thread. Display results are updated immediately after inference, *before* zone eval and emission. This prevents display stutter from backend/zone latency.
- **File sources** (`is_live=False`): Sampled frames are processed synchronously in the main loop to preserve frame ordering.
- EventBuilder creates payload(s) per sampled frame (single or list).
- Emitter delivers payload to destination.

Config
------
- ingest.fps_limit
- events.post_url

Edge Cases
----------
- If emitter fails, retry/skip policy applies.

Status
------
Implemented in `src/ai/pipeline/core.py`, `src/ai/pipeline/sampler.py`, and `src/ai/pipeline/emitter.py`.
Sequence diagram is still pending.

Code Mapping
------------
- Pipeline core: `src/ai/pipeline/core.py`
- Async processor: `src/ai/pipeline/processor.py`
- Emitters: `src/ai/pipeline/emitter.py`

## 한국어
동작
----
- Source에서 프레임을 지속적으로 읽는다.
- Sampler가 처리할 프레임을 결정한다.
- **라이브 소스** (`is_live=True`): `FrameProcessor`가 백그라운드 워커 스레드에서 추론을 수행한다. 추론 직후 디스플레이 결과를 즉시 갱신한 뒤 zone 평가/dedup/전송을 수행하여, 화면 표시가 백엔드 지연에 차단되지 않는다.
- **파일 소스** (`is_live=False`): 프레임 순서 보장을 위해 메인 루프에서 동기적으로 처리한다.
- EventBuilder가 샘플링된 프레임마다 페이로드(단일/리스트)를 생성한다.
- Emitter가 목적지로 페이로드를 전달한다.

설정
----
- ingest.fps_limit
- events.post_url

엣지 케이스
----------
- Emitter 실패 시 재시도/스킵 정책을 적용한다.

상태
----
`src/ai/pipeline/core.py`, `src/ai/pipeline/sampler.py`, `src/ai/pipeline/emitter.py`에 구현됨.
시퀀스 다이어그램은 추가 예정.

코드 매핑
---------
- 파이프라인 코어: `src/ai/pipeline/core.py`
- 비동기 프로세서: `src/ai/pipeline/processor.py`
- 에미터: `src/ai/pipeline/emitter.py`
