# Ops Runbook

## English

### Purpose

Runbook for running the AI pipeline in dev/prod and troubleshooting common issues.

### Quick Start (Docker)

1. Build: `docker build -t schnitzel-stream-platform .`
2. Run with snapshot volume: `docker run --rm -v <host_snapshot_dir>:/data/snapshots schnitzel-stream-platform`
3. Override config via env (example): `-e AI_LOG_LEVEL=DEBUG`
4. Note: container default command is `python -m schnitzel_stream` (posts to backend when reachable). For dry-run validation, pass `--dry-run` explicitly:
   `docker run --rm -v <host_snapshot_dir>:/data/snapshots schnitzel-stream-platform python -m schnitzel_stream --dry-run`
5. `--network host` is Linux-only. On Docker Desktop (Windows/macOS), use explicit port mapping.

### Local Run (host)

- Windows (Recommended): `./setup_env.ps1; python -m schnitzel_stream --dry-run`
- Linux/Bash: `PYTHONPATH=src python -m schnitzel_stream --dry-run`
- Webcam: `... --source-type webcam --camera-index 0 --dry-run`

### Logs

- Default log dir: `outputs/logs`
- Rotate by size: `AI_LOG_MAX_BYTES`, `AI_LOG_BACKUP_COUNT`
- Format: `AI_LOG_FORMAT=plain|json`
- Config-level overrides: `AI_LOGGING_LEVEL`, `AI_LOGGING_FORMAT`

### Common Issues

- **Backend not running**: retry warnings are expected; use `--dry-run` to avoid POST.
- **Backend down but resolvable**: pipeline keeps retrying by policy; confirm this is desired.
- **Multi-camera**: run one process/container per camera; logs include camera_id suffix.
- **RTSP unstable**: confirm reconnect/backoff settings in config.
- **Snapshots missing**: check `events.snapshot.base_dir` permissions.
- **Snapshots disabled**: ensure `events.snapshot.base_dir` is set.
- **Invalid camera/video input**: startup fails fast on unknown `--camera-id`, missing `--video` path, or invalid `--video` + `--source-type rtsp` combination.
- **RTSP E2E (host vs docker)**: host E2E requires `ffmpeg` installed locally; docker E2E still uses host `ffmpeg` to publish RTSP but runs pipeline in a container.

### Health Checks

- Metrics log: `ai.metrics`
- Heartbeat log: `ai.heartbeat`

### CI Gate (GitHub)

- Workflow: `.github/workflows/ci.yml`
  - Matrix test: Linux/Windows/macOS x Python 3.10/3.11
  - Aggregation job: `required-gate`
- Branch protection (GitHub Settings -> Branches):
  - Require status checks to pass before merging
  - Add required check: `required-gate`
  - Recommended: require branches to be up to date before merging

### Future Expansion Map

- Multi-camera scaling: process manager or single-process multi-cam (when scale grows).
- Ingest separation: dedicated ingest service + AI workers (queue/shared memory/RTSP restream).
- Model multi-branch: split models (person/PPE/smoke/fire) and merge detections.
- Tracker upgrade: DeepSORT/ReID for long-term ID stability.
- Rule expansion: PPE compliance, posture/fall, smoke/fire, composite rules.
- Performance: GPU multi-stream, TensorRT/ONNX optimization, batching/async.
- Observability: Prometheus/Grafana, centralized logs (ELK).
- Backend integration: ack/trace_id, queue-based delivery, retry policy hardening.

### Visualization (Dashboard)

- Streamlit-based real-time event/snapshot dashboard.
- Install:

  ```bash
  pip install -r requirements-dev.txt
  ```

- Run: `streamlit run demo/dashboard.py`
- Visualizes latest events by tailing `outputs/events.jsonl` by default.

### No-Hardware Checklist

- Run file-based pipeline with sample video (`data/samples/*.mp4`).
- Verify JSONL output with `--output-jsonl`.
- Run RTSP E2E scripts (local RTSP via MediaMTX + ffmpeg).
- RTSP E2E requires `ffmpeg` installed on the host.
- RTSP reconnect cycle test: `python scripts/check_rtsp.py` (cross-platform).
- Multi-camera smoke tests (legacy): see `scripts/legacy/` or use `scripts/multi_cam.py`.
- Confirm logs are written to `outputs/logs`.
- Confirm snapshots are created in `/tmp/snapshots` (or configured path).

---

## 한국어

### 목적

AI 파이프라인을 dev/prod에서 실행하고, 자주 발생하는 문제를 해결하기 위한 운영 메뉴얼(Runbook).

### 빠른 시작 (Docker)

1. 빌드: `docker build -t schnitzel-stream-platform .`
2. 스냅샷 볼륨 마운트하여 실행: `docker run --rm -v <host_snapshot_dir>:/data/snapshots schnitzel-stream-platform`
3. 환경 변수로 설정 오버라이드 (예시): `-e AI_LOG_LEVEL=DEBUG`
4. 참고: 컨테이너 기본 CMD는 `python -m schnitzel_stream`(백엔드 전송 경로)입니다. 드라이런 검증은 `--dry-run`을 명시하세요:
   `docker run --rm -v <host_snapshot_dir>:/data/snapshots schnitzel-stream-platform python -m schnitzel_stream --dry-run`
5. `--network host`는 Linux 전용입니다. Docker Desktop(Windows/macOS)에서는 포트 매핑을 사용하세요.

### 로컬 실행 (호스트 OS)

- 윈도우 (권장): `./setup_env.ps1; python -m schnitzel_stream --dry-run`
- 리눅스/Bash: `PYTHONPATH=src python -m schnitzel_stream --dry-run`
- 웹캠 테스트: `... --source-type webcam --camera-index 0 --dry-run`

### 로그 (Logs)

- 기본 로그 디렉터리: `outputs/logs` (루트 기준)
- 크기 기준 로테이션: `AI_LOG_MAX_BYTES`, `AI_LOG_BACKUP_COUNT`
- 로그 포맷: `AI_LOG_FORMAT=plain|json`
- 설정 레벨 오버라이드: `AI_LOGGING_LEVEL`, `AI_LOGGING_FORMAT`

### 자주 발생하는 문제

- **백엔드 서버 미동작**: 재시도 경고(warning) 발생은 정상이며, `--dry-run`으로 POST를 생략할 수 있음.
- **백엔드 서버 응답 없음(해석 가능)**: 정책에 따라 계속 재시도를 수행함.
- **멀티 카메라**: 카메라당 하나의 프로세스/컨테이너를 실행하며, 로그 파일명에 camera_id 접미사가 붙음.
- **RTSP 불안정**: 설정 파일의 reconnect/backoff 설정을 확인할 것.
- **스냅샷 누락**: `events.snapshot.base_dir` 디렉터리 권한 확인.
- **스냅샷 비활성화**: `events.snapshot.base_dir` 설정 여부 확인.
- **카메라/비디오 입력 오류**: 존재하지 않는 `--camera-id`, 유효하지 않은 `--video` 경로 등은 시작 시 즉시 실패함.
- **RTSP E2E (호스트 vs 도커)**: 호스트 E2E는 로컬 `ffmpeg`가 필요하며, 도커 환경에서도 RTSP 송출은 호스트의 `ffmpeg`를 사용함.

### 상태 확인 (Health Checks)

- 메트릭 로그: `ai.metrics`
- 하트비트 로그: `ai.heartbeat`

### CI 게이트 (GitHub)

- 워크플로: `.github/workflows/ci.yml`
  - 매트릭스 테스트: Linux/Windows/macOS x Python 3.10/3.11
  - 집계 잡: `required-gate`
- 브랜치 보호 설정(GitHub Settings -> Branches):
  - 머지 전에 상태 체크 통과 필수 활성화
  - 필수 체크에 `required-gate` 추가
  - 권장: 머지 전 최신 브랜치 동기화(require up to date) 활성화

### 시각화 (Dashboard)

- Streamlit 기반 실시간 이벤트/스냅샷 대시보드.
- 설치:

  ```bash
  pip install -r requirements-dev.txt
  ```

- 실행: `streamlit run demo/dashboard.py`
- 기본적으로 `outputs/events.jsonl` 파일을 추적하며 최신 이벤트를 시각화함.

### 실장비 없이 확인하는 방법 (체크리스트)

- 샘플 영상으로 파일 기반 파이프라인 실행 (`data/samples/*.mp4`).
- `--output-jsonl` 옵션으로 JSONL 출력 확인.
- RTSP E2E 스크립트 실행 (MediaMTX + ffmpeg 기반 로컬 RTSP).
- RTSP 재연결 사이클 테스트: `python scripts/check_rtsp.py`.
- 로그가 `outputs/logs`에 정상적으로 기록되는지 확인.
- 스냅샷이 지정된 경로(예: `/tmp/snapshots`)에 생성되는지 확인.
