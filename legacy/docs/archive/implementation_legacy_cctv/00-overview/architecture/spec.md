# Architecture - Spec

## English

Behavior
--------

- Source provides frames (file/rtsp).
- Sampler downsamples to target FPS.
- EventBuilder produces protocol-compliant payloads.
- Emitter delivers payloads (stdout/file/backend).

Config
------

- app: site_id, timezone
- ingest: fps_limit
- events: post_url, timeout, retry

Edge Cases
----------

- Initial source open failure may terminate startup; runtime read failures should retry without crashing core logic.
- Emitter failure should be handled by policy (retry/skip).

Status
------

Implemented in `src/ai/pipeline/core.py`, `src/ai/pipeline/sources/` (package), `src/ai/pipeline/sampler.py`,
and `src/ai/pipeline/emitter.py`. Keep this doc updated as modules evolve.

Code Mapping
------------

- Pipeline core: `src/ai/pipeline/core.py`
- Sources: `src/ai/pipeline/sources/`
- Sampler: `src/ai/pipeline/sampler.py`
- Emitters: `src/ai/pipeline/emitter.py`
- Ingest (future): `src/ai/ingest/README.md`

## 한국어

동작
----

- Source가 프레임을 제공(file/rtsp).
- Sampler가 목표 FPS로 다운샘플링.
- EventBuilder가 프로토콜 준수 페이로드를 생성.
- Emitter가 목적지로 전달(stdout/file/backend).

설정
----

- app: site_id, timezone
- ingest: fps_limit
- events: post_url, timeout, retry

엣지 케이스
----------

- 초기 소스 오픈 실패는 시작 단계에서 종료될 수 있으며, 런타임 read 실패는 코어 크래시 없이 재시도되어야 한다.
- Emitter 실패는 정책(재시도/스킵)에 따라 처리.

상태
----

`src/ai/pipeline/core.py`, `src/ai/pipeline/sources/` (패키지), `src/ai/pipeline/sampler.py`,
`src/ai/pipeline/emitter.py`에 구현됨. 모듈 변화에 따라 문서를 유지 관리.

코드 매핑
---------

- 파이프라인 코어: `src/ai/pipeline/core.py`
- 소스: `src/ai/pipeline/sources/`
- 샘플러: `src/ai/pipeline/sampler.py`
- 에미터: `src/ai/pipeline/emitter.py`
- Ingest(향후): `src/ai/ingest/README.md`
