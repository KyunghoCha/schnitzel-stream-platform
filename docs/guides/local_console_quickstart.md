# Local Console Quickstart

Last updated: 2026-02-17

## English

This guide is the canonical onboarding path for the local console stack.

## Standard 3-Step Path

1. `bootstrap`
2. `doctor`
3. `up` / `down`

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream

./setup_env.ps1 -Profile console -Manager pip -SkipDoctor
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform

./setup_env.sh --profile console --manager pip --skip-doctor
python3 scripts/stream_console.py doctor --strict --json
python3 scripts/stream_console.py up --allow-local-mutations
python3 scripts/stream_console.py status --json
python3 scripts/stream_console.py down
```

## Notes

- `up` runs in secure mode by default.
- `--allow-local-mutations` is a local-lab opt-in for mutating endpoints.
- If doctor fails, follow `suggested_fix` (PowerShell/Bash command pair).

## Advanced (Optional)

```bash
# API only
python scripts/stream_console.py up --api-only

# UI only
python scripts/stream_console.py up --ui-only

# custom ports/log dir
python scripts/stream_console.py up --api-port 18710 --ui-port 5180 --log-dir outputs/console_run_custom
```

Output paths:
- `outputs/console_run/control_api.log`
- `outputs/console_run/stream_console_ui.log`
- `outputs/console_run/pids/control_api.pid`
- `outputs/console_run/pids/stream_console_ui.pid`
- `outputs/console_run/console_state.json`

## 한국어

이 문서는 로컬 콘솔 스택 온보딩의 표준 경로다.

## 표준 3단계 경로

1. `bootstrap`
2. `doctor`
3. `up` / `down`

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream

./setup_env.ps1 -Profile console -Manager pip -SkipDoctor
python scripts/stream_console.py doctor --strict --json
python scripts/stream_console.py up --allow-local-mutations
python scripts/stream_console.py status --json
python scripts/stream_console.py down
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform

./setup_env.sh --profile console --manager pip --skip-doctor
python3 scripts/stream_console.py doctor --strict --json
python3 scripts/stream_console.py up --allow-local-mutations
python3 scripts/stream_console.py status --json
python3 scripts/stream_console.py down
```

## 참고

- `up`은 기본적으로 secure mode로 실행된다.
- `--allow-local-mutations`는 로컬 실습에서만 mutating endpoint를 여는 명시적 옵션이다.
- doctor 실패 시 `suggested_fix`에 출력되는 PowerShell/Bash 명령을 그대로 실행하면 된다.

## 고급 경로(선택)

```bash
# API만 실행
python scripts/stream_console.py up --api-only

# UI만 실행
python scripts/stream_console.py up --ui-only

# 포트/로그 경로 커스텀
python scripts/stream_console.py up --api-port 18710 --ui-port 5180 --log-dir outputs/console_run_custom
```

출력 경로:
- `outputs/console_run/control_api.log`
- `outputs/console_run/stream_console_ui.log`
- `outputs/console_run/pids/control_api.pid`
- `outputs/console_run/pids/stream_console_ui.pid`
- `outputs/console_run/console_state.json`
