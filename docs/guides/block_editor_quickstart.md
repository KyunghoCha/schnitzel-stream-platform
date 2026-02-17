# Block Editor Quickstart

Last updated: 2026-02-17

## English

This guide covers the hardened block editor flow in `apps/stream-console`.

## Scope

- Direct node drag/edit (`source` / `node` / `sink`)
- Handle-to-handle edge linking
- Node property editing (`id`, `kind`, `plugin`, `config`)
- Auto layout / align / fit-view actions
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

## Editor Flow (Mouse-First)

1. Open the `Editor` tab.
2. Click `Reload Profiles`, choose a profile, then click `Load Profile`.
3. Drag nodes on the canvas (position is reflected into the editor state).
4. Create edges by connecting node handles directly on canvas.
5. Use toolbar actions:
   - `Auto Layout`: deterministic DAG-layer layout (cycle-safe fallback)
   - `Align Horizontal`
   - `Align Vertical`
   - `Fit View`
6. Select a node and edit properties (`id`, `kind`, `plugin`, `config`) then click `Save Node`.
7. Run `Validate Graph` and check the validation badge (`ok/error`, node/edge counts, message).
8. Run `Run Graph` if validation is clean (mutating endpoint; requires token or local override).

Compatibility note:
- The manual `Add Edge` form is still available for one cycle, but the primary flow is direct handle connection.

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

이 문서는 `apps/stream-console`의 블록 에디터 하드닝 이후 사용 절차를 다룬다.

## 범위

- 노드 직접 드래그/편집(`source` / `node` / `sink`)
- 핸들 연결 기반 엣지 생성
- 노드 속성 편집(`id`, `kind`, `plugin`, `config`)
- 자동 정렬/정렬/화면 맞춤 액션
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

## Editor 사용 흐름(마우스 중심)

1. `Editor` 탭을 연다.
2. `Reload Profiles`로 목록을 갱신하고 프로필을 선택한 뒤 `Load Profile`을 누른다.
3. 캔버스에서 노드를 드래그해 위치를 조정한다.
4. 노드 핸들을 직접 연결해 엣지를 생성한다.
5. 툴바 액션을 사용한다.
   - `Auto Layout`: DAG 레이어 기반 자동 배치(사이클 포함 그래프도 안전 fallback)
   - `Align Horizontal`
   - `Align Vertical`
   - `Fit View`
6. 노드를 선택해 `id`, `kind`, `plugin`, `config`를 수정하고 `Save Node`를 누른다.
7. `Validate Graph` 실행 후 검증 배지(`ok/error`, 노드/엣지 수, 핵심 메시지)를 확인한다.
8. 검증이 통과하면 `Run Graph`를 실행한다(변경성 endpoint이므로 인증/override 정책 적용).

호환성 참고:
- 수동 `Add Edge` 폼은 1사이클 동안 유지되지만, 기본 조작 경로는 핸들 직접 연결이다.

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
