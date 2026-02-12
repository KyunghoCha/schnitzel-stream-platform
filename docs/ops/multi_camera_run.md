# Multi-Camera Runbook

## English

Purpose
-------

Run multiple cameras by launching one pipeline process/container per camera.

Recommended Approach
--------------------

- Use **one process per camera** (simplest operations, clean logs, easy restart).
- Define each camera under `configs/cameras.yaml` (merged from `configs/*.yaml`) → `cameras:`.
- Run one process per `camera_id` (CLI `--camera-id`).
- Use `id` as the primary key; `camera_id` is accepted for backward compatibility.

Examples (Host)
---------------

```bash
# Camera 1
PYTHONPATH=src python -m ai.pipeline --camera-id cam01 --source-type rtsp

# Camera 2
PYTHONPATH=src python -m ai.pipeline --camera-id cam02 --source-type rtsp
```

Automation (Host) - Cross-Platform / 크로스 플랫폼
-------------------------------------------------

```bash
# Start all enabled cameras from configs/cameras.yaml
# configs/cameras.yaml의 enabled 카메라 전체 실행
python scripts/multi_cam.py start

# Stop all managed camera processes
# 실행된 카메라 프로세스 종료
python scripts/multi_cam.py stop

# Check status / 상태 확인
python scripts/multi_cam.py status

# Start only a subset / 일부만 실행
python scripts/multi_cam.py start --cameras cam01,cam02

# With custom log directory / 커스텀 로그 디렉터리 사용
python scripts/multi_cam.py start --log-dir /path/to/logs

# With extra args for dry-run / dry-run 모드로 실행
python scripts/multi_cam.py start --extra-args "--dry-run"
```

> **Note**: Legacy bash scripts are preserved in `scripts/legacy/` for reference.
> bash 스크립트는 `scripts/legacy/`에 보관되어 있습니다.

Examples (Docker)
-----------------

> `--network host` is Linux-only. On Docker Desktop (Windows/macOS), use explicit port mapping.

```bash
# Camera 1
docker run --rm --network host \
  schnitzel-stream-platform python -m ai.pipeline --camera-id cam01 --source-type rtsp

# Camera 2
docker run --rm --network host \
  schnitzel-stream-platform python -m ai.pipeline --camera-id cam02 --source-type rtsp
```

Config Example
--------------

```yaml
cameras:
  - id: cam01
    enabled: true
    source:
      type: rtsp
      url: rtsp://cam1/stream
  - id: cam02
    enabled: true
    source:
      type: rtsp
      url: rtsp://cam2/stream
```

Notes
-----

- This project currently runs **one camera per process**.
- A multi-camera manager can be added later if needed.
- Avoid log collisions by relying on per-camera log filenames (camera_id suffix).
- Avoid snapshot collisions by using per-camera paths (`{site_id}/{camera_id}/...`) which are default.

Code Mapping
------------

- Entrypoint: `src/ai/pipeline/__main__.py`
- Config env overrides: `src/ai/config.py`

## 한국어

목적
-----

카메라별로 파이프라인 프로세스/컨테이너를 분리 실행하는 방식의 런북.

권장 방식
---------

- **카메라 1대 = 프로세스 1개** (운영 단순, 로그 분리, 재시작 쉬움)
- `configs/cameras.yaml`(또는 `configs/*.yaml`)의 `cameras:`에 카메라별 설정을 넣는다.
- 카메라마다 `camera_id`를 지정하고 `--camera-id`로 실행한다.
- 기본 키는 `id`이며, 하위 호환을 위해 `camera_id`도 허용한다.

예시 (Host)
------------

```bash
# Camera 1
PYTHONPATH=src python -m ai.pipeline --camera-id cam01 --source-type rtsp

# Camera 2
PYTHONPATH=src python -m ai.pipeline --camera-id cam02 --source-type rtsp
```

자동화(Host) - 크로스 플랫폼
----------------------------

```bash
# configs/cameras.yaml의 enabled 카메라 전체 실행
python scripts/multi_cam.py start

# 실행된 카메라 프로세스 종료
python scripts/multi_cam.py stop

# 상태 확인
python scripts/multi_cam.py status

# 일부만 실행
python scripts/multi_cam.py start --cameras cam01,cam02

# 커스텀 로그 디렉터리 사용
python scripts/multi_cam.py start --log-dir /path/to/logs

# dry-run 모드로 실행
python scripts/multi_cam.py start --extra-args "--dry-run"
```

> **참고**: 기존 bash 스크립트는 `scripts/legacy/`에 보관되어 있습니다.

예시 (Docker)
-------------

> `--network host`는 Linux에서만 안정적으로 동작합니다. Docker Desktop(Windows/macOS)에서는 포트 매핑 방식을 사용하세요.

```bash
# Camera 1
docker run --rm --network host \
  schnitzel-stream-platform python -m ai.pipeline --camera-id cam01 --source-type rtsp

# Camera 2
docker run --rm --network host \
  schnitzel-stream-platform python -m ai.pipeline --camera-id cam02 --source-type rtsp
```

설정 예시
---------

```yaml
cameras:
  - id: cam01
    enabled: true
    source:
      type: rtsp
      url: rtsp://cam1/stream
  - id: cam02
    enabled: true
    source:
      type: rtsp
      url: rtsp://cam2/stream
```

노트
-----

- 현재 프로젝트는 **카메라 1대 = 프로세스 1개** 구조이다.
- 필요 시 멀티 카메라 매니저를 추가할 수 있다.
- 로그 파일명에 camera_id가 포함되어 충돌을 방지한다.
- 스냅샷 경로는 `{site_id}/{camera_id}/...` 구조라 카메라 간 충돌이 없다.

코드 매핑
---------

- 엔트리포인트: `src/ai/pipeline/__main__.py`
- 설정 env 오버라이드: `src/ai/config.py`
