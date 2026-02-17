# Local Console Quickstart

Last updated: 2026-02-17

## English

This guide starts the local control API + web console stack with one command surface.

## 3-Step Quick Path

1. `doctor`
2. `up`
3. `down`

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream
$env:PYTHONPATH = "src"

python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform
export PYTHONPATH=src

python3 scripts/stream_console.py doctor --strict --json
python3 scripts/stream_console.py up --allow-local-mutations
python3 scripts/stream_console.py status --json
python3 scripts/stream_console.py down
```

## Secure Mode Notes

- Default behavior keeps mutating endpoints blocked in local-only mode.
- `--allow-local-mutations` is explicit local-lab opt-in for mutating endpoints.
- Use `--token <value>` on `up` to set `SS_CONTROL_API_TOKEN` in API process env.

## Common Commands

```bash
# API only
python scripts/stream_console.py up --api-only

# UI only
python scripts/stream_console.py up --ui-only

# custom ports/log dir
python scripts/stream_console.py up --api-port 18710 --ui-port 5180 --log-dir outputs/console_run_custom
```

## Output Paths

- API log: `outputs/console_run/control_api.log`
- UI log: `outputs/console_run/stream_console_ui.log`
- API pid: `outputs/console_run/pids/control_api.pid`
- UI pid: `outputs/console_run/pids/stream_console_ui.pid`
- state file: `outputs/console_run/console_state.json`

## 한국어

이 가이드는 로컬 Control API + 웹 콘솔 스택을 단일 명령면으로 실행하는 빠른 시작 문서다.

## 3단계 빠른 경로

1. `doctor`
2. `up`
3. `down`

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream
$env:PYTHONPATH = "src"

python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform
export PYTHONPATH=src

python3 scripts/stream_console.py doctor --strict --json
python3 scripts/stream_console.py up --allow-local-mutations
python3 scripts/stream_console.py status --json
python3 scripts/stream_console.py down
```

## 보안 모드 참고

- 기본 동작은 로컬 모드에서 mutating endpoint를 차단한다.
- `--allow-local-mutations`는 로컬 실습용 명시적 opt-in 옵션이다.
- `up`에서 `--token <value>`를 주면 API 프로세스 env에 `SS_CONTROL_API_TOKEN`이 설정된다.

## 자주 쓰는 명령

```bash
# API만 실행
python scripts/stream_console.py up --api-only

# UI만 실행
python scripts/stream_console.py up --ui-only

# 포트/로그 경로 커스텀
python scripts/stream_console.py up --api-port 18710 --ui-port 5180 --log-dir outputs/console_run_custom
```

## 출력 경로

- API 로그: `outputs/console_run/control_api.log`
- UI 로그: `outputs/console_run/stream_console_ui.log`
- API pid: `outputs/console_run/pids/control_api.pid`
- UI pid: `outputs/console_run/pids/stream_console_ui.pid`
- 상태 파일: `outputs/console_run/console_state.json`
