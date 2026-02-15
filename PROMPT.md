# Handoff Prompt (schnitzel-stream-platform)

## English

You are continuing work on the runtime pipeline repo `schnitzel-stream-platform`.

### Repo purpose

- CCTV AI runtime pipeline (ingest -> build events -> emit)
- Supports RTSP/file sources, mock backend, snapshot policy, metrics/heartbeat
- Model adapters are optional (YOLO/ONNX) and can be merged

### Current Status (2026-02-10)

- **Async Frame Processing — Display-First (2026-02-10)**: `FrameProcessor` runs inference in a background worker thread. Display results are updated immediately after inference, *before* zone eval and emission, preventing display stutter from zone API fetch latency. Auto-selected via `source.is_live`.
- **Sensor Lane P2 Baseline (2026-02-10)**: Sensor lane now supports nearest attachment (`payload.sensor`) plus optional independent `SENSOR_EVENT` and `FUSED_EVENT` outputs with sensor/fusion metrics fields.
- **Full Codebase Audit Completed (2026-02-09)**: 169 items reviewed across 10 categories (G1-G10). All critical/major bugs fixed. Latest local verification: 154 passed (2026-02-10), regression verified.
- **Test Hygiene Baseline Added (2026-02-10)**: Added cross-platform static hygiene checker `scripts/test_hygiene.py` to detect duplicate/low-signal tests, and connected a CI ratchet gate to prevent metric regression.
- **Document Consistency Audit (2026-02-09)**: 150+ markdown files cross-referenced against source code. 9 inconsistencies found and all resolved. Quality score: 100/100.
- **Contract Docs Simplified (2026-02-09)**: Contract references were streamlined around protocol/model-interface/class-taxonomy SSOT docs.
- **Grand Verification & Recovery Completed (2026-02-08)**: Full pipeline dry-run passed. Korean encoding corruption fully recovered.
- **Multimodal Roadmap Added**: Section 6 (Multi-Sensor Integration) added to `docs/future/future_roadmap.md` for ultrasonic/IoT sensor fusion.
- **Engine Throttling & Loop Added (2026-02-08)**: File-based infinite loop (`--loop`) and core FPS throttling implemented and promoted to official spec.

### Working Principles

- Follow this repository's `PROMPT.md` as the execution standard and output template SSOT.
- Apply cross-cutting changes: update code, docs, configs, and tests in the same change-set.
- Prefer root-cause fixes over tactical patches; avoid accumulating technical debt.
- Maintain architectural consistency and long-term maintainability (clean boundaries, explicit contracts).
- Prevent doc/code drift; enforce SSOT alignment.
- Make assumptions explicit; validate when uncertainty exists.
- Preserve repository conventions; avoid ad-hoc structure or path hardcoding.
- Prioritize tests by operational risk (fault paths, retries, reconnection, failure handling).
- Keep decision boundaries explicit: runtime emits evidence/events, while final hazard/alarm judgment belongs to user policy by default (backend policy layer is optional) unless explicitly implemented in runtime.
- When adding features, update SSOT first, then implement.
- Before making changes, re-read the relevant files to confirm current state.
- If asked for doc/code alignment, follow the established method: read in full, compare to code, update all related docs/configs/tests, and record changes consistently.
- If any contract/interface changes occur, update `docs/contracts/protocol.md` and relevant SSOT docs (`docs/specs/model_interface.md`, `docs/specs/model_class_taxonomy.md`), and sync external docs if they reference the contract.

### Key docs to read first

1. `docs/index.md`
2. `docs/contracts/protocol.md`
3. `docs/specs/legacy_pipeline_spec.md`
4. `docs/ops/ops_runbook.md`

### Not done yet / external

- Real backend integration tests
- Real device RTSP tuning
- Production model accuracy validation

### Can do before policy lock

- Test/automation hardening (RTSP reconnect E2E, multi-camera ops scripts, snapshot failure tests)
- Static test hygiene checks and threshold tuning (`scripts/test_hygiene.py`)
- Internal doc/code consistency checks and updates
- Local-only model inference/visualization verification (no label/final taxonomy changes)
- Update progress logs and PROMPT status after changes

### Recent changes to be aware of

- **Async Frame Processing — Display-First (2026-02-10)**: `FrameProcessor` runs inference in a background worker thread with display-first pattern: inference → immediate display update → zone eval → dedup → emit. Display FPS is independent of zone/backend latency. Auto-selected via `source.is_live`.
- **ThreadedSource for Live Sources (2026-02-09)**: Live sources (RTSP/webcam) are now automatically wrapped with `ThreadedSource`, which reads frames in a dedicated background thread. This prevents frame drops and video corruption caused by model inference blocking `source.read()`.
- **Engine Throttling & Loop (2026-02-08)**: Added `--loop` to `FileSource` and implemented deterministic FPS throttling in the pipeline core to ensure stable file-based benchmarking/demo.
- **Live Source Latency Fix (2026-02-08)**: Disabled FPS throttling for `is_live=True` sources to prevent buffer bloat. Forced `CAP_FFMPEG` backend. Removed `nobuffer` flag to prevent decoding errors on streams with B-frames. (`flags=low_delay` was planned but not implemented -- deferred to future optimization.)
- **RTSP Stability & Transport Control (2026-02-08)**: Enforced `tcp` transport by default to prevent video corruption (packet loss) on high-res streams. Exposed `AI_RTSP_TRANSPORT` env var for optional UDP switching. Also fixed infinite loop issues during initial RTSP connection.
- **Config Precedence Fix (2026-02-08)**: Fixed environment variable overrides being ignored due to profile merge order. Env vars now always take precedence over all yaml configs.
- **AI_ZONES_SOURCE Env Var (2026-02-08)**: Added `AI_ZONES_SOURCE` environment variable override to dynamically switch between `file` and `api` zone sources at runtime.
- **Multi-Camera Visualization Fix (2026-02-09)**: Updated `OpencvVisualizer` initialization to include `camera_id` in the window name. This prevents window collisions when running multiple pipelines concurrently with `--visualize`.
- **Visualization Buffer Staining Fix (2026-02-09)**: Modified `OpencvVisualizer` to draw detections on a copy of the frame instead of in-place. This prevents "ghost" or "stained" boxes from previous frames appearing in subsequent ones due to OpenCV's buffer reuse policy.
- **Smooth Visualization (2026-02-08)**: Decoupled visualization from sampling; all frames are now displayed with retained detection boxes to prevent flickering.
- **Korean Encoding Recovery (2026-02-08)**: Fully reconstructed and repaired broken Korean characters in `legacy_pipeline_spec.md` (formerly `pipeline_spec.md`), `protocol.md`, `ops_runbook.md`, and other spec documents to ensure UTF-8 (No BOM) integrity.
- **Multimodal Sensor Roadmap (2026-02-08)**: Added technical vision for integrating non-vision sensors (Ultrasonic, IoT) into the pipeline core.
- **Cross-platform script migration (2026-02-07)**: All bash scripts replaced with Python equivalents.
  - `scripts/multi_cam.py`, `scripts/check_rtsp.py`, `scripts/process_manager.py`.
- **Test Hygiene Checker Added (2026-02-10)**: Added `scripts/test_hygiene.py` for static duplicate/no-assert/trivial-assert detection with optional strict mode and CI ratchet thresholds.
- **Future Roadmap Added (2026-02-07)**: Detailed roadmap for Multi-camera Orchestration, Self-learning, and Performance Optimization added to `docs/future/future_roadmap.md`.
- Zones API negative cache/backoff implemented.
- ONNX adapter NMS class mapping alignment fixed.
- CLI source validation hardened (`camera_id` fail-fast).

---

## 한국어

당신은 런타임 파이프라인 레포 `schnitzel-stream-platform` 작업을 이어서 진행합니다.

### 레포 목적

- CCTV AI 런타임 파이프라인(ingest -> 이벤트 생성 -> 전송)
- RTSP/파일 소스 지원, mock 백엔드, 스냅샷 정책, metrics/heartbeat 포함
- 모델 어댑터는 선택사항(YOLO/ONNX)이며 병합 가능

### 현재 상태 (2026-02-10)

- **비동기 프레임 처리 — Display-First (2026-02-10)**: `FrameProcessor`가 백그라운드 워커 스레드에서 추론을 수행합니다. 추론 직후 디스플레이 결과를 즉시 갱신한 뒤 zone 평가와 전송을 수행하여, zone API fetch 지연이 화면 표시를 차단하지 않습니다. `source.is_live` 기준 자동 분기.
- **센서 축 P2 기반 (2026-02-10)**: 최근 센서 패킷 주입(`payload.sensor`)에 더해, 선택적으로 독립 `SENSOR_EVENT` 및 `FUSED_EVENT` 출력과 센서/융합 메트릭 필드를 지원합니다.
- **전체 코드 감사 완료 (2026-02-09)**: 169개 항목을 10개 카테고리(G1-G10)로 검토. 모든 critical/major 버그 수정. 최신 로컬 검증: 154개 통과 (2026-02-10), 회귀 검증 완료.
- **테스트 위생 점검 기준 추가 (2026-02-10)**: 중복/저신호 테스트를 탐지하는 크로스 플랫폼 정적 점검 도구 `scripts/test_hygiene.py`를 추가하고, CI 래칫 게이트로 지표 악화를 차단.
- **문서 정합성 전수 조사 (2026-02-09)**: 150+ 마크다운 파일을 소스 코드와 교차 대조. 9건 불일치 발견 및 전부 해결. 품질 점수: 100/100.
- **계약 문서 단순화 (2026-02-09)**: 계약 관련 기준 문서를 protocol/model_interface/class_taxonomy 중심으로 정리.
- **한글 인코딩 완벽 복구 (2026-02-08)**: 손상되었던 모든 주요 문서의 UTF-8 무결성 확보.
- **멀티 센서 로드맵 추가**: 초음파 및 IoT 센서 결합 멀티모달 AI 확장 계획 수립.
- **엔진 루프 및 FPS 제어 추가 (2026-02-08)**: 파일 소스 무한 반복(`--loop`) 및 코어 FPS 제어 로직을 정식 사양으로 반영.

### 작업 원칙

- 실행 표준/출력 템플릿 SSOT는 이 레포의 `PROMPT.md`를 따른다.
- 코드 수정 시 관련 문서/설정/테스트를 동일 체인지셋으로 동시 갱신한다.
- 단기 패치가 아닌 근본 원인 해결을 우선하여 기술부채 누적을 방지한다.
- 아키텍처 일관성 및 장기 유지보수성을 보장한다(경계/계약 명확화).
- 문서-코드 드리프트를 금지하고 SSOT 정합성을 유지한다.
- 가정은 명시하고 불확실성은 검증한다.
- 레포 관례/구조를 유지하고 임의 구조/경로 하드코딩을 지양한다.
- 테스트는 운영 리스크 중심(실패 경로/재시도/재연결/오류 처리)으로 우선순위화한다.
- 판단 경계를 명시한다: 런타임은 근거 이벤트를 생성/전달하고, 최종 위험/알람 판단은 기본적으로 사용자 운영 정책에서 수행한다. (백엔드 정책 계층은 선택 사항, 런타임 명시 구현 시 예외)
- 기능 추가 시 SSOT 업데이트를 선행한 뒤 구현한다.
- 변경 전 관련 파일을 다시 읽어 최신 상태를 확인한다.
- 문서-코드 정합성 요청 시 기존 방식대로: 문서 정독 → 코드 비교 → 관련 문서/설정/테스트 동시 갱신 → 일관성 기록.
- 계약/인터페이스 변경 시 `docs/contracts/protocol.md`와 관련 SSOT(`docs/specs/model_interface.md`, `docs/specs/model_class_taxonomy.md`)를 갱신하고 외부 참조 문서를 동기화한다.

### 우선 읽을 문서

1. `docs/index.md`
2. `docs/contracts/protocol.md`
3. `docs/specs/legacy_pipeline_spec.md`
4. `docs/ops/ops_runbook.md`

### 아직 미완 / 외부 의존

- 실제 백엔드 통합 테스트
- 실장비 RTSP 튜닝
- 프로덕션 모델 정확도 검증

### 정책 확정 전까지 가능한 작업

- 테스트/자동화 보강(RTSP 재연결 E2E, 멀티카메라 운영 스크립트, 스냅샷 실패 케이스 테스트)
- 정적 테스트 위생 점검 및 임계치 보정(`scripts/test_hygiene.py`)
- 문서↔코드 정합성 내부 점검 및 갱신
- 로컬 모델 추론/시각화 확인(라벨/최종 taxonomy 변경 제외)
- 변경 후 진행 로그 및 PROMPT 상태 업데이트

### 최근 변경 사항

- **비동기 프레임 처리 — Display-First (2026-02-10)**: `FrameProcessor`가 백그라운드 워커 스레드에서 추론 수행. display-first 패턴: 추론 → 디스플레이 즉시 갱신 → zone 평가 → dedup → emit. 디스플레이 FPS가 zone/백엔드 지연에 독립적. `source.is_live` 기준 자동 분기.
- **라이브 소스 ThreadedSource 적용 (2026-02-09)**: 라이브 소스(RTSP/웹캠)에 `ThreadedSource`를 자동 적용하여 프레임 수신을 백그라운드 스레드로 분리. 모델 추론 중 `source.read()` 블로킹으로 인한 프레임 드롭/영상 깨짐을 방지합니다.
- **엔진 루프 및 FPS 제어 추가 (2026-02-08)**: 파일 기반 무한 반복 분석 기능과 목표 FPS에 맞춘 실행 속도 제어 로직을 구현하여 데모/테스트 안정성을 확보했습니다.
- **라이브 소스 지연 해결 (2026-02-08)**: `CAP_FFMPEG` 백엔드 강제 사용, FPS 스로틀링 해제로 TCP 사용 시에도 지연/끊김 없는 RTSP 수신을 구현했습니다. (`nobuffer` 옵션은 디코딩 에러를 유발하여 제거, `flags=low_delay`는 미구현 -- 향후 최적화로 이관)
- **RTSP 안정화 및 전송 제어 (2026-02-08)**: 고해상도 영상 깨짐(패킷 손실)을 완벽히 방지하기 위해 기본 전송을 `tcp`로 강제하고, 필요 시 `AI_RTSP_TRANSPORT` 환경 변수로 `udp` 전환이 가능하도록 수정했습니다. 무한 연결 대기 버그도 수정됨.
- **설정 우선순위 버그 수정 (2026-02-08)**: 프로필 병합 순서로 인해 환경 변수가 무시되던 문제를 수정했습니다. 이제 환경 변수가 모든 yaml 설정보다 우선 적용됩니다.
- **AI_ZONES_SOURCE 환경 변수 추가 (2026-02-08)**: 런타임에 `file` 또는 `api` 간 zone 소스를 동적으로 전환할 수 있는 환경 변수 오버라이드를 추가했습니다.
- **멀티 카메라 시각화 수정 (2026-02-09)**: 여러 파이프라인을 동시에 실행할 때 시각화 창이 겹치거나 사라지는 문제를 해결하기 위해, 창 이름에 `camera_id`를 포함하도록 수정했습니다.
- **시각화 버그 수정 (2026-02-09)**: OpenCV의 프레임 버퍼 재사용으로 인한 잔상 문제(Buffer Staining)를 방지하기 위해, 시각화 시 프레임 복사본을 만들어 그리도록 수정했습니다.
- **부드러운 시각화 (2026-02-08)**: 시각화를 샘플링에서 분리하여 모든 프레임을 표시하고, 탐지 박스를 유지하여 깜빡임을 방지합니다.
- **한글 인코딩 복구 (2026-02-08)**: 깨져 있던 핵심 문서들의 한글 텍스트를 전수 복구하고, 임시 복구 스크립트를 제거하여 레포지토리 청결도를 확보했습니다.
- **멀티 센서 및 멀티모달 로드맵 추가 (2026-02-08)**: 시각 외 센서(초음파, IoT)를 결합한 상황 인지 능력 확장 계획을 `future_roadmap.md` 및 `roadmap.md`에 반영했습니다.
- **크로스 플랫폼 스크립트 마이그레이션 (2026-02-07)**: 모든 bash 스크립트를 Python으로 대체. (`scripts/multi_cam.py`, `scripts/check_rtsp.py` 등)
- **테스트 위생 점검 도구 추가 (2026-02-10)**: `scripts/test_hygiene.py`를 추가해 정적 기준(중복/무검증/`assert True`)을 점검하고, CI 래칫 임계치로 수치 악화를 방지할 수 있게 했습니다.
- **미래 로드맵 수립 (2026-02-07)**: 다중 카메라 오케스트레이션, 자율 학습, 성능 최적화 로드맵 추가.
- Zones API 네거티브 캐시/백오프 구현.
- ONNX 어댑터 NMS 클래스 매핑 정합성 수정.
- CLI 소스 검증 강화(`camera_id` 즉시 실패 로직 등).

### 다음 단계

- 필요 시 테스트 확장 또는 실장비/백엔드 통합 검증 추가.

### 리뷰에서 나온 보완 항목(미처리)

- 최신 로컬 검수 기준 미처리 항목 없음.
