# Block Editor Quickstart

Last updated: 2026-02-17

## English

This guide covers the block editor MVP in `apps/stream-console`.

## Scope

- Node placement/editing (`source` / `node` / `sink`)
- Edge linking
- Node property editing (`id`, `kind`, `plugin`, `config`)
- YAML import/export
- Graph validate/run through Control API

## 3-Step Start

1. Bootstrap dependencies
2. Start local console stack
3. Open Editor tab

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream
$env:PYTHONPATH = "src"

python scripts/bootstrap_env.py --profile console --manager pip
python scripts/stream_console.py up --allow-local-mutations
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform
export PYTHONPATH=src

python3 scripts/bootstrap_env.py --profile console --manager pip
python3 scripts/stream_console.py up --allow-local-mutations
```

Open:
- UI: `http://127.0.0.1:5173`
- API: `http://127.0.0.1:18700/api/v1/health`

## Editor Flow

1. Open the `Editor` tab.
2. Click `Reload Profiles` and select a graph profile.
3. Click `Load Profile` (optional; starts from template profile).
4. Add/remove nodes and edges.
5. Edit selected node properties and click `Save Node`.
6. Use `Export YAML` / `Import YAML` for round-trip checks.
7. Click `Validate Graph`.
8. Click `Run Graph` (mutating endpoint; requires token or local override).

## API Endpoints Used by Editor

- `GET /api/v1/graph/profiles?experimental=<bool>`
- `POST /api/v1/graph/from-profile`
- `POST /api/v1/graph/validate`
- `POST /api/v1/graph/run`

## Security Notes

- `graph.run` is a mutating endpoint.
- Default P17 policy blocks mutating endpoints without bearer in no-token mode.
- Local lab override for one cycle: `--allow-local-mutations` (sets `SS_CONTROL_API_ALLOW_LOCAL_MUTATIONS=true`).

## Stop Stack

```bash
python scripts/stream_console.py down
```

---

## 한국어

이 문서는 `apps/stream-console`의 블록 에디터 MVP 사용 절차를 다룬다.

## 범위

- 노드 배치/편집(`source` / `node` / `sink`)
- 엣지 연결
- 노드 속성 편집(`id`, `kind`, `plugin`, `config`)
- YAML import/export
- Control API 기반 그래프 validate/run

## 3단계 시작

1. 의존성 부트스트랩
2. 로컬 콘솔 스택 기동
3. Editor 탭 접속

## Windows PowerShell

```powershell
cd C:\Projects\schnitzel-stream-platform
conda activate schnitzel-stream
$env:PYTHONPATH = "src"

python scripts/bootstrap_env.py --profile console --manager pip
python scripts/stream_console.py up --allow-local-mutations
```

## Linux / macOS (bash)

```bash
cd /mnt/c/Projects/schnitzel-stream-platform
export PYTHONPATH=src

python3 scripts/bootstrap_env.py --profile console --manager pip
python3 scripts/stream_console.py up --allow-local-mutations
```

접속 주소:
- UI: `http://127.0.0.1:5173`
- API: `http://127.0.0.1:18700/api/v1/health`

## Editor 사용 흐름

1. `Editor` 탭을 연다.
2. `Reload Profiles`로 프로필 목록을 갱신한다.
3. 필요하면 `Load Profile`로 템플릿 그래프를 불러온다.
4. 노드/엣지를 추가 또는 제거한다.
5. 선택한 노드 속성을 편집한 뒤 `Save Node`를 누른다.
6. `Export YAML` / `Import YAML`로 round-trip을 확인한다.
7. `Validate Graph`를 실행한다.
8. `Run Graph`를 실행한다(변경성 endpoint이므로 인증/override 정책 적용).

## Editor가 사용하는 API

- `GET /api/v1/graph/profiles?experimental=<bool>`
- `POST /api/v1/graph/from-profile`
- `POST /api/v1/graph/validate`
- `POST /api/v1/graph/run`

## 보안 참고

- `graph.run`은 mutating endpoint다.
- P17 기본 정책상 token 없는 모드에서는 mutating endpoint가 차단된다.
- 로컬 실습은 1사이클 한정으로 `--allow-local-mutations`를 사용한다.

## 종료

```bash
python scripts/stream_console.py down
```
