# Progress Log

## English

Last Updated: 2026-02-10

### Recent Activities (2026-02-10)

- **Root Upgrade (config/runtime consistency)**:
  - Fixed `.env.example` adapter path (`ai.vision.adapters.custom_adapter:CustomModelAdapter`).
  - Config loader now merges `default.yaml` + `cameras.yaml` first, then selected profile only (`dev` or `prod`), preventing unintended profile bleed.
  - Config-relative paths are resolved against repo root for deterministic execution across different working directories.
  - Added `SourceSettings.index` and webcam index resolution priority: CLI `--camera-index` > camera config `source.index` > 0.
  - Added config validation for duplicate camera IDs and invalid webcam `source.index` type.
- **Intent Annotation**:
  - Added explicit `intent:` comments in core runtime paths to distinguish intentional policy (low-latency/live latest-only, dry-run fallback) from accidental behavior.
- **Documentation Sync**:
  - Synced README/spec/ops docs with latest behavior and execution standard.
  - Updated latest local verification result: `154 passed` (2026-02-10).
- **Test Hygiene Baseline Added**:
  - Added cross-platform static checker `scripts/test_hygiene.py` to detect duplicate test bodies and low-signal tests (`no assert`, trivial `assert True`).
  - Added command references and testing docs for hygiene execution and optional strict thresholds.
  - Added CI ratchet gate (`.github/workflows/ci.yml`) to fail only when hygiene metrics regress.
- **Cross-Platform Hardening**:
  - Added GitHub Actions OS matrix test workflow (`.github/workflows/ci.yml`) for Linux/Windows/macOS.
  - Added stable CI aggregation check `required-gate` for branch protection.
  - Unified script default log dir to OS temp dir via `tempfile.gettempdir()` (`check_rtsp.py`, `multi_cam.py`).
  - Added MediaMTX architecture mapping for Linux/macOS arm64 and documented Docker `--network host` Linux-only scope.
- **Compatibility/Quality Follow-up**:
  - Added Python 3.10-compatible tar extraction fallback in `scripts/check_rtsp.py` while preserving safe extraction checks.
  - Updated protocol/agreement metrics schema examples to match runtime keys (`events_accepted`, `backend_ack_ok`, `backend_ack_fail`).
  - Updated ONNX optional dependency test to use `pytest.importorskip(..., exc_type=ImportError)` for pytest 9.1 compatibility.
- **Runtime Policy Upgrade**:
  - Switched default runtime mode to `real` and set default adapter to `ai.vision.adapters.custom_adapter:CustomModelAdapter`.
  - `CustomModelAdapter` is now fail-fast template behavior (prevents accidental fake event emission before implementation).
  - Removed unknown `model.mode` implicit fallback (`DummyEventBuilder`) and changed to fail-fast.
  - Locked regression/RTSP stability scripts to explicit `AI_MODEL_MODE=mock` for deterministic test path.
- **Emitter Extensibility Upgrade**:
  - Added dynamic output emitter loader `load_event_emitter()` (`module:ClassName`).
  - Added `events.emitter_adapter` + `AI_EVENTS_EMITTER_ADAPTER` override.
  - Split emitter implementation into `src/ai/pipeline/emitters/` package and kept `src/ai/pipeline/emitter.py` as compatibility shim.
  - Kept runtime precedence: `--output-jsonl` > `--dry-run` > custom emitter plugin > backend emitter.
- **Source Extensibility Upgrade**:
  - Added dynamic input source loader `load_frame_source()` (`module:ClassName`).
  - Added `source.adapter` + `AI_SOURCE_ADAPTER` and `source.type` + `AI_SOURCE_TYPE` override path.
  - Added `source.type=plugin` runtime path with fail-fast validation for missing adapter.
- **ROS2 Plugin Template Added**:
  - Added optional ROS2 source plugin `ai.plugins.ros2.image_source:Ros2ImageSource`.
  - Added optional ROS2 emitter plugin `ai.plugins.ros2.event_emitter:Ros2EventEmitter`.
  - Added ROS2 plugin env examples and command references in `.env.example`, `README.md`, and `docs/ops/command_reference.md`.
- **Multimodal Architecture Baseline Added**:
  - Added `docs/design/multimodal_pipeline_design.md` for video+sensor runtime design.
  - Defined two-lane input architecture (`VideoSource` + `SensorSource`) with a single fusion boundary.
  - Fixed roadmap wording to avoid overloading `FrameSource`; future sensor expansion now uses dedicated sensor lane.
- **Sensor Lane P2 Baseline Implemented**:
  - Added independent `SENSOR_EVENT` emission policy (`sensor.emit_events`, `AI_SENSOR_EMIT_EVENTS`).
  - Added optional `FUSED_EVENT` emission policy (`sensor.emit_fused_events`, `AI_SENSOR_EMIT_FUSED_EVENTS`).
  - Added sensor/fusion metrics fields (`sensor_packets_total`, `sensor_packets_dropped`, `sensor_source_errors`, `fusion_*`) and heartbeat sensor age.
- **Observability Upgrade (No-hardware path)**:
  - Split metrics semantics: emitter-accepted count (`events`/`events_accepted`) vs real backend delivery ACK (`backend_ack_ok`/`backend_ack_fail`).
  - Added backend emitter callback path + unit tests to verify ACK success/failure counting.

### Recent Activities (2026-02-09)

- **ThreadedSource Implementation**: Added `ThreadedSource` wrapper that decouples frame reading into a background thread. Live sources (RTSP/webcam) are automatically wrapped at pipeline startup. Prevents frame drops and decoder corruption caused by model inference blocking `source.read()`. 6 new unit tests added.
- **Full Codebase Audit & Remediation**: Executed a 169-item audit across all source files, docs, configs, and tests. Root-cause fixes applied for all Critical/Major items (G1-G10).
  - **G1**: Fixed `_coerce_env_value()` type casting bug, added 5 missing env var mappings (`AI_LOG_LEVEL`, `AI_LOG_FORMAT`, `AI_LOG_MAX_BYTES`, `AI_LOG_BACKUP_COUNT`, `AI_MODEL_ADAPTER`), wired log rotation params through settings dataclass.
  - **G2**: Activated dead heartbeat code via `_emit_telemetry()` in pipeline loop. Removed `NotImplementedModelAdapter` dead code. Added consecutive failure detection to `CompositeModelAdapter`.
  - **G3**: Centralized `resolve_project_root()` (DRY). Fixed `regression_check.py` to use `tempfile.gettempdir()` + `sys.executable` for cross-platform support.
  - **G4**: Split ONNX adapter `infer()` (78 lines) into 4 focused methods (SRP). Extracted PERSON hardcode in tracker to configurable `_REQUIRE_TRACK_TYPES`.
  - **G5**: Fixed mock_backend default bind `0.0.0.0` -> `127.0.0.1`. Added SIGTERM -> SIGKILL escalation in `process_manager.py`. Made RTSP test URL/port configurable via env vars.
  - **G6**: Moved `AI_MODEL_ADAPTER` from `os.getenv()` to `settings.model.adapter` (DI pattern). Added warning log for missing source path fallback.
  - **G7**: Added 14 new tests (emitter 4, env_override 9, adapter loader 1). Fixed `test_golden.py` to use `pytest.skip()`.
  - **G8**: Documented 4xx non-retry policy in `legacy_pipeline_spec.md` (formerly `pipeline_spec.md`). Reorganized `.env.example` with all env vars.
  - **G9**: Fixed float `==` comparison in `zones.py` with `math.isclose()`. Added JSON type validation. Replaced private field access with `get_stale()` method.
  - **G10**: Full test suite (60 tests) passed. Regression check passed.

### Recent Activities (2026-02-08)

- **Engine Enhancement**: Added `--loop` functionality to `FileSource` and implemented core-level FPS throttling for stable local benchmarking.
- **Korean Encoding Recovery**: Fully reconstructed and audited broken Korean text in all major specification and operation documents (`legacy_pipeline_spec.md` (formerly `pipeline_spec.md`), `protocol.md`, etc.).
- **Multimodal AI Roadmap**: Defined the technical design for integrating ultrasonic/IoT sensors into the vision pipeline.

### Completed Tests

- Unit/Integration: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q` -> **154 passed** (2026-02-10).
  - Previous: 60 passed (2026-02-09). Additional regression-prevention tests were added.
- Regression (golden): `python scripts/regression_check.py` -> regression_ok.
  - Snapshots: `/tmp/snapshots_regression_test`
- RTSP E2E (host): `scripts/check_rtsp.py` (Linux: `scripts/legacy/rtsp_e2e_stability.sh`) -> reconnect recovered.
  - Example result: `count_before=3`, `count_after=9`.
  - Logs: `/tmp/ai_pipeline_e2e_rtsp_stability`
  - Mock backend log: `/tmp/ai_pipeline_e2e_rtsp_stability/mock_backend.log` (port 18080)
- RTSP E2E (docker): `scripts/legacy/rtsp_e2e_stability_docker.sh` (Requires Docker) -> reconnect recovered.
  - Example result: `count_before=3`, `count_after=9`.
  - Logs: `/tmp/ai_pipeline_e2e_rtsp_stability_docker`
- RTSP reconnect cycle: `scripts/check_rtsp.py` (Linux: `scripts/legacy/rtsp_e2e_reconnect_cycle.sh`) -> reconnect recovered.
  - Example result: `count_before=3`, `count_after=8`.
  - Logs: `/tmp/ai_pipeline_e2e_rtsp_reconnect`
- Multi-camera smoke (rtsp+file): `scripts/multi_cam.py` (Linux: `scripts/legacy/multi_camera_smoke.sh`) -> both cameras emit.
  - Example result: `cam01_events=5`, `cam02_events=5`.
  - Logs: `/tmp/ai_pipeline_multi_cam`
- Dual RTSP smoke (rtsp x2): `scripts/multi_cam.py` (Linux: `scripts/legacy/rtsp_multi_cam_dual.sh`) -> both cameras emit.
  - Example result: `cam01_events=5`, `cam02_events=5`.
  - Logs: `/tmp/ai_pipeline_rtsp_multi_cam`
- Tracker (IOU): `TRACKER_TYPE=iou` -> stable track_id assigned.
- RTSP recent reconnect unit test: `tests/unit/pipeline/test_rtsp_recent_reconnect.py` -> pass.
- RTSP max attempts unit tests: `tests/unit/pipeline/test_rtsp_max_attempts.py` -> pass.

### Completed Tests (continued)

- Model E2E (multi-adapter): YOLO(pt) + ONNX together -> emit ok.
  - Example: `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter,ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter` with sample video.
- Model E2E (multi-adapter + tracker): YOLO(pt) + ONNX + IOU tracker -> emit ok.
  - Example: `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter,ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter` + `TRACKER_TYPE=iou`.

### Key Artifacts

- Logs: `outputs/logs/` (latest run file)
- RTSP host logs: `/tmp/ai_pipeline_e2e_rtsp_stability`
- RTSP docker logs: `/tmp/ai_pipeline_e2e_rtsp_stability_docker`

### Notes

- Ops runbook: `docs/ops/ops_runbook.md`
- Snapshot policy: `docs/ops/snapshot_policy.md`
- Multi-model merge supported via comma-separated `AI_MODEL_ADAPTER`
- RTSP E2E scripts export `LOG_DIR` to keep event counting stable in strict shells.
- RTSP E2E scripts export `CHECK_PORT` so mock backend port checks work in subprocesses.
- Docker E2E requires docker socket access; ensure the user is in the `docker` group or run with sudo if permission is denied.
- RTSP E2E scripts use `PYTHON_BIN` (default `python3`) to avoid sudo PATH issues.
- Docker RTSP E2E re-run (sudo + PYTHON_BIN) recovered: `count_before=3`, `count_after=9` (2026-02-06).
- Protocol updated with local-only validation status and agreement-required items (2026-02-06).
- Performance roadmap: `docs/ops/ai/performance_optimization.md`
- Model training plan: `docs/ops/ai/model_training_plan.md`
- Labeling guide: `docs/ops/ai/labeling_guide.md`
- Training report template: `docs/ops/ai/training_report_template.md`
- Class taxonomy draft: `docs/specs/model_class_taxonomy.md`
- Class mapping draft: `configs/model_class_map.yaml` (optional)
- Class mapping now applied to YOLO/ONNX adapters via `MODEL_CLASS_MAP_PATH`.
- Accuracy validation guide: `docs/ops/ai/accuracy_validation.md`
- Accuracy eval script template: `scripts/accuracy_eval.py`
- ByteTrack optional tracker (fallback to IOU when deps missing).
- Protocol v0.2 draft includes PPE/POSTURE/HAZARD event types.
- Docs alignment: protocol/model_interface/model_yolo_run updated for current scope and PPE demo class map paths.
- ONNX adapter NMS mapping bug fixed: class_id now stays aligned with kept bbox after NMS.
- CLI/source validation hardened:
  - invalid `camera_id` now fails fast
  - `--video` now forces file source and fails fast on missing file path
  - `--video` + `--source-type rtsp` is rejected at startup
- **Cross-platform Script Migration (2026-02-07)**: All legacy bash scripts migrated to Python (`scripts/*.py`).
- **Future Roadmap Added (2026-02-07)**: Detailed roadmap for Multi-camera, Self-learning, and Performance Optimization added to `docs/roadmap/future_backlog.md`.
- **Final Polishing & Audit (2026-02-07)**: Full markdown linting cleared, link integrity verified, and Windows environment script `setup_env.ps1` added.

### Current State Summary

- Local-only scope (no real device/backend): complete and reproducible.
- RTSP E2E (host/docker), multi-camera automation, and mock backend flow verified.
- Model adapters (YOLO/ONNX), multi-adapter merge, class mapping, tracker baseline validated.
- **Full audit remediation complete** (2026-02-09): 60 unit/integration tests passing, regression_ok.

### Blocked by External Environment

- Real RTSP device not available (param tuning deferred).
- Backend service not available (real POST integration deferred).
- Model integration baseline complete; advanced trackers (DeepSORT) pending.

### Code Mapping

- Tests: `tests/unit/`, `tests/integration/`, `tests/regression/`
- RTSP E2E: `scripts/check_rtsp.py`, `scripts/multi_cam.py`
- Mock backend: `src/ai/pipeline/mock_backend.py`

## 한국어

마지막 업데이트: 2026-02-10

### 최근 활동 (2026-02-10)

- **루트 업그레이드(설정/런타임 정합성)**:
  - `.env.example` 어댑터 경로 수정 (`ai.vision.adapters.custom_adapter:CustomModelAdapter`).
  - 설정 로더를 `default.yaml` + `cameras.yaml` + 선택 프로파일(`dev`/`prod`) 순으로 정리해 프로파일 누수 방지.
  - 설정 상대경로를 repo root 기준으로 해석하도록 통일.
  - `SourceSettings.index` 추가 및 웹캠 인덱스 우선순위 명확화: CLI `--camera-index` > 카메라 설정 `source.index` > 0.
  - 중복 camera ID, 잘못된 webcam index 타입 검증 추가.
- **의도 주석 명시**:
  - 런타임 핵심 경로에 `의도:` 주석을 추가해 저지연 정책/폴백 정책을 결함과 구분 가능하게 정리.
- **테스트 위생 점검 기준 추가**:
  - 크로스 플랫폼 정적 점검 도구 `scripts/test_hygiene.py`를 추가해 중복 본문/저신호 테스트(`assert` 없음, `assert True`)를 탐지할 수 있게 함.
  - 명령 레퍼런스 및 테스트 문서에 위생 점검 실행/엄격 모드 기준을 반영.
  - CI 래칫 게이트(`.github/workflows/ci.yml`)를 추가해 위생 지표가 나빠질 때만 실패하도록 구성.
- **크로스 플랫폼 보강**:
  - GitHub Actions OS 매트릭스 테스트 워크플로 추가 (`.github/workflows/ci.yml`, Linux/Windows/macOS).
  - 브랜치 보호에 사용할 고정 CI 집계 체크 `required-gate` 추가.
  - `check_rtsp.py`, `multi_cam.py`의 기본 로그 경로를 `tempfile.gettempdir()` 기반으로 통일.
  - MediaMTX 아키텍처 매핑에 Linux/macOS arm64 대응 추가, Docker `--network host`의 Linux 전용 범위를 운영 문서에 명시.
- **호환성/품질 후속 보강**:
  - `scripts/check_rtsp.py`에 Python 3.10 호환 tar 추출 fallback 추가(안전 추출 검증 유지).
  - 프로토콜/협의 문서의 메트릭 예시를 런타임 키(`events_accepted`, `backend_ack_ok`, `backend_ack_fail`)와 일치하도록 정렬.
  - pytest 9.1 호환을 위해 ONNX 선택 의존 테스트에 `pytest.importorskip(..., exc_type=ImportError)` 반영.
- **런타임 정책 업그레이드**:
  - 런타임 기본 모드를 `real`로 전환하고 기본 어댑터를 `ai.vision.adapters.custom_adapter:CustomModelAdapter`로 설정.
  - `CustomModelAdapter`는 구현 전 가짜 이벤트 방출을 막기 위해 fail-fast 템플릿 동작으로 변경.
  - 미지원 `model.mode`의 암묵 fallback(`DummyEventBuilder`) 제거 후 fail-fast로 전환.
  - 회귀/RTSP 안정성 스크립트는 결정성 유지를 위해 `AI_MODEL_MODE=mock`를 명시적으로 고정.
- **Emitter 확장성 업그레이드**:
  - 출력 emitter 동적 로더 `load_event_emitter()` (`module:ClassName`) 추가.
  - `events.emitter_adapter` + `AI_EVENTS_EMITTER_ADAPTER` 오버라이드 추가.
  - emitter 구현을 `src/ai/pipeline/emitters/` 패키지로 분리하고 `src/ai/pipeline/emitter.py`는 호환 shim으로 유지.
  - 런타임 우선순위 유지: `--output-jsonl` > `--dry-run` > 커스텀 emitter 플러그인 > backend emitter.
- **Source 확장성 업그레이드**:
  - 입력 source 동적 로더 `load_frame_source()` (`module:ClassName`) 추가.
  - `source.adapter` + `AI_SOURCE_ADAPTER`, `source.type` + `AI_SOURCE_TYPE` 오버라이드 경로 추가.
  - `source.type=plugin` 실행 경로 및 adapter 누락 시 fail-fast 검증 추가.
- **ROS2 플러그인 템플릿 추가**:
  - 선택형 ROS2 입력 플러그인 `ai.plugins.ros2.image_source:Ros2ImageSource` 추가.
  - 선택형 ROS2 출력 플러그인 `ai.plugins.ros2.event_emitter:Ros2EventEmitter` 추가.
  - `.env.example`, `README.md`, `docs/ops/command_reference.md`에 ROS2 플러그인 환경변수/실행 예시 반영.
- **멀티모달 아키텍처 기준 추가**:
  - 영상+센서 런타임 설계 문서 `docs/design/multimodal_pipeline_design.md` 추가.
  - 입력 2축(`VideoSource` + `SensorSource`) + 단일 fusion 경계 원칙 정의.
  - `FrameSource` 과적재를 피하도록 로드맵 표현을 `SensorSource` 전용 축 기준으로 수정.
- **센서 축 P2 기반 구현**:
  - 독립 `SENSOR_EVENT` 전송 정책(`sensor.emit_events`, `AI_SENSOR_EMIT_EVENTS`)을 추가.
  - 선택적 `FUSED_EVENT` 전송 정책(`sensor.emit_fused_events`, `AI_SENSOR_EMIT_FUSED_EVENTS`)을 추가.
  - 센서/융합 메트릭 필드(`sensor_packets_total`, `sensor_packets_dropped`, `sensor_source_errors`, `fusion_*`)와 heartbeat 센서 age를 추가.
- **관측성 업그레이드 (무실장비 경로)**:
  - 메트릭 의미를 분리: 에미터 수락 카운트(`events`/`events_accepted`)와 실제 백엔드 전달 ACK(`backend_ack_ok`/`backend_ack_fail`).
  - BackendEmitter callback 경로와 ACK 성공/실패 카운트 단위 테스트 추가.

### 최근 활동 (2026-02-09)

- **ThreadedSource 구현**: 프레임 수신을 백그라운드 스레드로 분리하는 `ThreadedSource` 래퍼를 추가. 라이브 소스(RTSP/웹캠)는 파이프라인 시작 시 자동으로 래핑됨. 모델 추론이 `source.read()`를 블로킹하여 발생하는 프레임 드롭/디코더 깨짐을 방지. 신규 단위 테스트 6건 추가.
- **전수 코드베이스 감사 및 근본 수정**: 소스/문서/설정/테스트 전 파일 대상 169건 감사 수행. Critical/Major 이슈 전건 근본 해결 (G1-G10).
  - **G1**: `_coerce_env_value()` 타입 변환 버그 수정, 누락 환경변수 매핑 5건 추가 (`AI_LOG_LEVEL`, `AI_LOG_FORMAT`, `AI_LOG_MAX_BYTES`, `AI_LOG_BACKUP_COUNT`, `AI_MODEL_ADAPTER`), 로그 로테이션 파라미터를 settings 데이터클래스로 연결.
  - **G2**: 미호출 하트비트 코드를 `_emit_telemetry()`로 파이프라인 루프에 활성화. `NotImplementedModelAdapter` 데드코드 제거. `CompositeModelAdapter`에 연속 실패 감지 추가.
  - **G3**: `resolve_project_root()` 공용화(DRY). `regression_check.py`에 `tempfile.gettempdir()` + `sys.executable` 적용으로 크로스 플랫폼 호환.
  - **G4**: ONNX 어댑터 `infer()` (78줄)을 4개 메서드로 분리(SRP). 트래커의 PERSON 하드코딩을 설정 가능한 `_REQUIRE_TRACK_TYPES`로 추출.
  - **G5**: mock_backend 기본 바인드 `0.0.0.0` → `127.0.0.1` 수정. `process_manager.py`에 SIGTERM → SIGKILL 에스컬레이션 추가. RTSP 테스트 URL/포트 환경변수 설정 가능.
  - **G6**: `AI_MODEL_ADAPTER`를 `os.getenv()`에서 `settings.model.adapter`로 이동(DI 패턴). 소스 경로 미존재 시 경고 로그 추가.
  - **G7**: 14개 신규 테스트 추가 (에미터 4, env_override 9, 어댑터 로더 1). `test_golden.py`에 `pytest.skip()` 적용.
  - **G8**: `legacy_pipeline_spec.md`(기존 `pipeline_spec.md`)에 4xx 비재시도 정책 문서화. `.env.example` 전면 재정리.
  - **G9**: `zones.py` 부동소수점 `==` 비교를 `math.isclose()`로 수정. JSON 타입 검증 추가. private 필드 접근을 `get_stale()` 공개 메서드로 대체.
  - **G10**: 전체 테스트 (60개) 통과 확인. 회귀 검증 통과.

### 최근 활동 (2026-02-08)

- **엔진 기능 강화**: 파일 소스 무한 루프(`--loop`) 기능 추가 및 코어 FPS 제어(Throttling) 구현으로 로컬 테스트 및 데모 안정성 확보.
- **한글 인코딩 복구**: 주요 명세서 및 운영 문서의 깨진 한글 텍스트 전수 복구 및 무결성 검증 완료.
- **멀티모달 AI 로드맵**: 초음파/IoT 센서 데이터를 결합한 상황 인지 능력 확장 설계를 `future_backlog.md`에 반영.

### 완료된 테스트

- Unit/Integration: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q` -> **154개 통과** (2026-02-10).
  - 이전: 60개 통과 (2026-02-09). 회귀 방지 테스트를 추가 반영.
- Regression (golden): `python scripts/regression_check.py` -> regression_ok.
  - 스냅샷: `/tmp/snapshots_regression_test`
- RTSP E2E (host): `scripts/check_rtsp.py` (Linux: `scripts/legacy/rtsp_e2e_stability.sh`) -> 재연결 후 복구.
  - 예시 결과: `count_before=3`, `count_after=9`.
  - 로그: `/tmp/ai_pipeline_e2e_rtsp_stability`
  - Mock 백엔드 로그: `/tmp/ai_pipeline_e2e_rtsp_stability/mock_backend.log` (포트 18080)
- RTSP E2E (docker): `scripts/legacy/rtsp_e2e_stability_docker.sh` (Docker 필요) -> 재연결 후 복구.
  - 예시 결과: `count_before=3`, `count_after=9`.
  - 로그: `/tmp/ai_pipeline_e2e_rtsp_stability_docker`
- RTSP 재연결 반복: `scripts/check_rtsp.py` (Linux: `scripts/legacy/rtsp_e2e_reconnect_cycle.sh`) -> 재연결 후 복구.
  - 예시 결과: `count_before=3`, `count_after=8`.
  - 로그: `/tmp/ai_pipeline_e2e_rtsp_reconnect`
- 멀티 카메라 스모크(rtsp+file): `scripts/multi_cam.py` (Linux: `scripts/legacy/multi_camera_smoke.sh`) -> 두 카메라 모두 emit 확인.
  - 예시 결과: `cam01_events=5`, `cam02_events=5`.
  - 로그: `/tmp/ai_pipeline_multi_cam`
- 듀얼 RTSP 스모크(rtsp x2): `scripts/multi_cam.py` (Linux: `scripts/legacy/rtsp_multi_cam_dual.sh`) -> 두 카메라 모두 emit 확인.
  - 예시 결과: `cam01_events=5`, `cam02_events=5`.
  - 로그: `/tmp/ai_pipeline_rtsp_multi_cam`
- 트래커(IOU): `TRACKER_TYPE=iou` -> track_id 안정 부여 확인.
- RTSP 최근 재연결 단위 테스트: `tests/unit/pipeline/test_rtsp_recent_reconnect.py` -> 통과.
- RTSP max_attempts 단위 테스트: `tests/unit/pipeline/test_rtsp_max_attempts.py` -> 통과.

### 완료된 테스트(추가)

- 모델 E2E(멀티 어댑터): YOLO(pt) + ONNX 병합 -> emit 정상.
  - 예시: 샘플 영상에 `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter,ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter` 적용.
- 모델 E2E(멀티 어댑터 + 트래커): YOLO(pt) + ONNX + IOU 트래커 -> emit 정상.
  - 예시: `AI_MODEL_ADAPTER=ai.vision.adapters.yolo_adapter:YOLOAdapter,ai.vision.adapters.onnx_adapter:ONNXYOLOAdapter` + `TRACKER_TYPE=iou`.

### 주요 산출물

- 로그: `outputs/logs/` (최근 실행 파일)
- RTSP host 로그: `/tmp/ai_pipeline_e2e_rtsp_stability`
- RTSP docker 로그: `/tmp/ai_pipeline_e2e_rtsp_stability_docker`

### 노트

- 운영 런북: `docs/ops/ops_runbook.md`
- 스냅샷 정책: `docs/ops/snapshot_policy.md`
- 다중 모델 병합 지원: `AI_MODEL_ADAPTER` 콤마 구분
- RTSP E2E 스크립트는 `LOG_DIR`를 export하여 이벤트 카운트가 안정적으로 유지되도록 한다.
- RTSP E2E 스크립트는 `CHECK_PORT`를 export하여 포트 체크가 하위 프로세스에서도 동작하도록 한다.
- Docker E2E는 docker 소켓 권한이 필요하므로, 권한 오류 시 `docker` 그룹 추가 또는 sudo로 실행해야 한다.
- RTSP E2E 스크립트는 `PYTHON_BIN`(기본 `python3`)을 사용해 sudo 환경의 PATH 이슈를 피한다.
- Docker RTSP E2E 재실행(sudo + PYTHON_BIN) 복구 확인: `count_before=3`, `count_after=9` (2026-02-06).
- 프로토콜에 로컬 단독 검증 상태/합의 필요 항목을 추가(2026-02-06).
- 성능 로드맵: `docs/ops/ai/performance_optimization.md`
- 모델 학습 계획: `docs/ops/ai/model_training_plan.md`
- 라벨링 가이드: `docs/ops/ai/labeling_guide.md`
- 학습 리포트 템플릿: `docs/ops/ai/training_report_template.md`
- 클래스 분류 초안: `docs/specs/model_class_taxonomy.md`
- 클래스 매핑 초안: `configs/model_class_map.yaml` (선택)
- 클래스 매핑은 `MODEL_CLASS_MAP_PATH`로 YOLO/ONNX 어댑터에 적용됨.
- 정확도 검증 가이드: `docs/ops/ai/accuracy_validation.md`
- 정확도 평가 스크립트 템플릿: `scripts/accuracy_eval.py`
- ByteTrack 선택 트래커(의존성 없으면 IOU로 폴백).
- 프로토콜 v0.2 초안에 PPE/POSTURE/HAZARD 이벤트 타입 포함.
- 문서/코드 정합성 테스트 추가: drops, heartbeat camera_id, empty zones, PERSON track_id.
- 문서 정합성: protocol/model_interface/model_yolo_run를 현재 범위와 PPE 데모 경로로 업데이트.
- ONNX 어댑터 NMS 매핑 버그 수정: NMS 이후 유지된 bbox와 class_id 정합성 보장.
- CLI/소스 검증 강화:
  - 잘못된 `camera_id`는 즉시 실패
  - `--video`는 file 소스로 강제되며 파일 경로 미존재 시 즉시 실패
  - `--video` + `--source-type rtsp` 조합은 시작 시 거부
- PROMPTS 기준 정합성 점검(2026-02-06): implementation 전 디렉토리 확인, 신규 불일치 없음.
- 테스트 실행(2026-02-06): 46 passed (이후 2026-02-09 감사 작업에서 14개 추가, 2026-02-10 업그레이드 작업에서 추가 확장)
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q` -> 154 passed (2026-02-10 최신)
  - `python scripts/regression_check.py` -> regression_ok
- **크로스 플랫폼 스크립트 마이그레이션 (2026-02-07)**: 모든 bash 스크립트를 Python으로 전환하여 윈도우/리눅스 호환성 확보.
- **미래 로드맵 추가 (2026-02-07)**: 다중 카메라 오케스트레이션 및 자율 학습 설계를 담은 상세 로드맵(`docs/roadmap/future_backlog.md`) 추가.
- **최종 폴리싱 및 감사 (2026-02-07)**: 전수 마크다운 린트 교정, 링크 무결성 검증, 윈도우용 `setup_env.ps1` 추가.

### 현재 상태 요약

- 로컬 단독 환경(실장비/백엔드 없음): 완료 및 재현 가능.
- RTSP E2E(host/docker), 멀티카메라 자동화, mock 백엔드 흐름 검증 완료.
- 모델 어댑터(YOLO/ONNX), 멀티 어댑터 병합, 클래스 매핑, 트래커 베이스라인 검증 완료.
- **전수 감사 수정 완료 + 후속 업그레이드 반영** (2026-02-10): 단위/통합 테스트 154개 통과, 회귀 검증 통과.

### 외부 환경 부재로 보류

- 실장비 RTSP 부재로 파라미터 튜닝 보류.
- 백엔드 서비스 부재로 실제 POST 통합 테스트 보류.
- 모델 기준 연동 완료, 고급 트래커(DeepSORT)는 보류.

### 코드 매핑

- 테스트: `tests/unit/`, `tests/integration/`, `tests/regression/`
- RTSP E2E: `scripts/check_rtsp.py`, `scripts/multi_cam.py`
- Mock 백엔드: `src/ai/pipeline/mock_backend.py`
