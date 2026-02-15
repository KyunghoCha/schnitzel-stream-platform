# Handoff Prompt (schnitzel-stream-platform)

Last updated: 2026-02-15

Current step id (SSOT): `P8.2` (see `docs/roadmap/execution_roadmap.md`)

## English

This file is the stable handoff entrypoint.

Canonical pivot rules/status live in:

- `PROMPT_CORE.md` (platform pivot rules + current status)
- `docs/roadmap/execution_roadmap.md` (execution SSOT: ordered plan + step id)

Legacy CCTV pipeline prompt (archived): `PROMPT_LEGACY.md`

Key facts:

- Stable runtime entrypoint: `python -m schnitzel_stream`
- Legacy runtime: `legacy/ai/**` (import path `ai.*` via `src/ai` shim)

Latest snapshot:

- Last completed: `P8.1` RTSP source plugin + tests + demo graph (commits: `8cf52e8`, `471ff6c`)
- Next: `P8.2` Webcam source plugin + tests + demo graph

Verification (local):

- Minimal syntax check: `python3 -m compileall -q src tests`
- Full tests (after deps): `pip install -r requirements-dev.txt` then `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`

---

## 한국어

이 파일은 핸드오프를 위한 안정적인 엔트리 문서입니다.

플랫폼 피벗의 기준(규칙/상태)은 아래에 있습니다:

- `PROMPT_CORE.md` (플랫폼 피벗 규칙 + 현재 상태)
- `docs/roadmap/execution_roadmap.md` (실행 SSOT: 계획 + step id)

레거시 CCTV 파이프라인 프롬프트(보관): `PROMPT_LEGACY.md`

핵심 사실:

- 안정 엔트리포인트: `python -m schnitzel_stream`
- 레거시 런타임: `legacy/ai/**` (`src/ai` shim으로 import 경로 `ai.*` 유지)

최신 스냅샷:

- 최근 완료: `P8.1` RTSP source 플러그인 + 테스트 + 데모 그래프 (commits: `8cf52e8`, `471ff6c`)
- 다음: `P8.2` Webcam source 플러그인 + 테스트 + 데모 그래프

검증(로컬):

- 최소 문법 체크: `python3 -m compileall -q src tests`
- 전체 테스트(의존성 설치 후): `pip install -r requirements-dev.txt` 다음 `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
