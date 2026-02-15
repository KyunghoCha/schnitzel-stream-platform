# pipeline_design

## English

Pipeline Design (File/RTSP -> AI -> Backend)
=================================================

Goal
----

Provide a modular AI pipeline that reads frames from file or RTSP, builds events, and emits them to the backend.

Inputs Used for Alignment
-------------------------

- `docs/packs/vision/event_protocol_v0.2.md`: event schema and API contract
- `docs/packs/vision/model_interface.md`: model/tracker output contract

High-level Flow
---------------

1) Source ingest (`FileSource` or `RtspSource`)
2) Frame sampling (`FrameSampler`)
3) Event build (real-first; mock explicit for tests) aligned to `docs/packs/vision/event_protocol_v0.2.md`
4) Dedup (optional)
5) Emit (`BackendEmitter`/`StdoutEmitter`/`FileEmitter`) to `/api/events`

### Async Frame Processing — Display-First (Live Sources)

For live sources (`is_live=True`: RTSP, webcam), frame processing runs in a background worker thread (`FrameProcessor`) to prevent display stutter. The worker updates display results immediately after inference, *before* zone evaluation and emission.
When `zones.source=api`, zone data refresh is non-blocking (background refresh + cache-first evaluation) to keep inference paths resilient during temporary API outages.

For file sources (`is_live=False`), synchronous processing is maintained to ensure ordered frame-by-frame processing.

Data Flow Diagram (text)
------------------------

**File source (synchronous):**

FrameSource -> FrameSampler -> EventBuilder -> Dedup -> EventEmitter -> backend API

**Live source (asynchronous, display-first):**

```
[Main Thread]     FrameSource -> FrameSampler -> submit(frame) -> Visualizer.show()
                                                     |                  ↑
                                                     v                  | (immediate)
[Worker Thread]               EventBuilder(inference) → update display → zone eval → dedup → emit
```

Key Decisions
-------------

- Modular interfaces for source, sampler, builder, emitter
- File-first ingest with RTSP option
- Frame sampling via `ingest.fps_limit`
- Sampling only (no in-process buffer/queue)
- Timezone-aware timestamps
- Snapshot save optional via config

Current Scope (2026-02-09)
--------------------------

- Non-model pipeline is implemented end-to-end.
- Model adapters (YOLO/ONNX), multi-model merge, and IOU tracker are integrated (ByteTrack optional).
- Full codebase audit completed (G1-G10): 169 items reviewed, critical/major bugs fixed, latest local verification 153 passed, 2 skipped (2026-02-11).
- Remaining work: production model integration and real RTSP device validation.
- Planned multimodal (video+sensor) extension is documented separately in `legacy/docs/legacy/design/multimodal_pipeline_design.md`.

Code Mapping
------------

- Sources: `src/ai/pipeline/sources/` (file.py, rtsp.py, webcam.py)
- Sampler: `src/ai/pipeline/sampler.py`
- Event builders: `src/ai/pipeline/events.py`
- Async processor: `src/ai/pipeline/processor.py`
- Dedup: `src/ai/rules/dedup.py`
- Emitters: `src/ai/pipeline/emitters/` (compat shim: `src/ai/pipeline/emitter.py`)
- Optional runtime plugins (example): `src/ai/plugins/ros2/` (`Ros2ImageSource`, `Ros2EventEmitter`)
- Legacy pipeline core: `src/ai/pipeline/core.py`
- Phase 0 wiring (legacy job): `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- Entrypoint: `src/schnitzel_stream/cli/__main__.py`

## 한국어

파이프라인 설계 (File/RTSP -> AI -> Backend)
==================================================

목표
----

파일 또는 RTSP에서 프레임을 읽고 이벤트를 생성한 뒤 백엔드로 전송하는 모듈형 AI 파이프라인을 제공한다.

정렬 기준 입력
--------------

- `docs/packs/vision/event_protocol_v0.2.md`: 이벤트 스키마 및 API 계약
- `docs/packs/vision/model_interface.md`: 모델/트래커 출력 계약

상위 수준 흐름
--------------

1) 소스 인제스트 (`FileSource` 또는 `RtspSource`)
2) 프레임 샘플링 (`FrameSampler`)
3) 이벤트 생성 (실사용 우선, mock은 테스트 시 명시적으로만 사용, `docs/packs/vision/event_protocol_v0.2.md` 기준)
4) 중복 억제(선택)
5) `/api/events`로 전송 (`BackendEmitter`/`StdoutEmitter`/`FileEmitter`)

### 비동기 프레임 처리 — Display-First (라이브 소스)

라이브 소스(`is_live=True`: RTSP, 웹캠)에서는 백그라운드 워커 스레드(`FrameProcessor`)에서 프레임을 처리하여 디스플레이 끊김을 방지한다. 워커는 추론 직후 디스플레이 결과를 즉시 갱신한 뒤, zone 평가와 전송을 수행한다.
`zones.source=api`인 경우 zone 데이터는 비차단 방식(백그라운드 갱신 + 캐시 우선 평가)으로 처리하여 API 일시 장애가 추론 경로를 직접 막지 않도록 한다.

파일 소스(`is_live=False`)에서는 순서대로 프레임을 처리해야 하므로 기존 동기 처리를 유지한다.

데이터 흐름(텍스트)
-------------------

**파일 소스 (동기):**

FrameSource -> FrameSampler -> EventBuilder -> Dedup -> EventEmitter -> backend API

**라이브 소스 (비동기, display-first):**

```
[메인 스레드]     FrameSource -> FrameSampler -> submit(frame) -> Visualizer.show()
                                                      |                  ↑
                                                      v                  | (즉시)
[워커 스레드]                EventBuilder(추론) → display 갱신 → zone eval → dedup → emit
```

핵심 결정
---------

- source/sampler/builder/emitter를 모듈형 인터페이스로 분리
- 파일 우선 ingest + RTSP 옵션
- `ingest.fps_limit` 기반 프레임 샘플링
- 샘플링만 수행(프로세스 내부 버퍼/큐 없음)
- 타임존 인식 타임스탬프
- 설정으로 스냅샷 저장을 선택 가능

현재 범위 (2026-02-09)
----------------------

- 모델 제외 파이프라인은 end-to-end 구현 완료.
- 모델 어댑터(YOLO/ONNX), 다중 모델 병합, IOU 트래커 연동 완료(ByteTrack 선택).
- 전체 코드 감사 완료(G1-G10): 169개 항목 검토, critical/major 버그 수정, 최신 로컬 검증 153개 통과, 2개 스킵 (2026-02-11).
- 남은 작업: 프로덕션 모델 연동, 실장비 RTSP 검증.
- 계획된 멀티모달(영상+센서) 확장 설계는 `legacy/docs/legacy/design/multimodal_pipeline_design.md`에 분리 문서화.

코드 매핑
---------

- 소스: `src/ai/pipeline/sources/` (file.py, rtsp.py, webcam.py)
- 샘플러: `src/ai/pipeline/sampler.py`
- 이벤트 빌더: `src/ai/pipeline/events.py`
- 비동기 프로세서: `src/ai/pipeline/processor.py`
- Dedup: `src/ai/rules/dedup.py`
- 에미터: `src/ai/pipeline/emitters/` (호환 shim: `src/ai/pipeline/emitter.py`)
- 선택 런타임 플러그인(예시): `src/ai/plugins/ros2/` (`Ros2ImageSource`, `Ros2EventEmitter`)
- 레거시 파이프라인 코어: `src/ai/pipeline/core.py`
- Phase 0 연결(레거시 job): `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
