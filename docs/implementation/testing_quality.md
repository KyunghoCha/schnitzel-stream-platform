# Testing and Quality Gates

Last updated: 2026-02-18

## English

## Test Pyramid (Current)

- Unit tests: graph/runtime/node behavior
- Integration tests: durable queue replay, end-to-end graph behavior
- Regression: v2 golden output comparison

## Active Test Locations

- Unit: `tests/unit/`
- Integration: `tests/integration/`
- Regression: `tests/regression/`

## Baseline Commands

- compile gate: `python3 -m compileall -q src tests scripts`
- pytest gate (when env ready):
  - `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`

## Reliability Smoke (P24)

- quick mode:
  - `python3 scripts/reliability_smoke.py --mode quick --json`
- full mode:
  - `python3 scripts/reliability_smoke.py --mode full`

Quick mode focuses on durable reliability regressions:
- `tests/unit/test_sqlite_queue.py`
- `tests/unit/nodes/test_durable_sqlite_nodes.py`
- `tests/integration/test_durable_queue_replay.py`
- `tests/integration/test_durable_queue_reliability.py`

Full mode extends quick mode with:
- `tests/integration/test_v2_durable_queue_idempotency_e2e.py`

## Policy

Any runtime behavior change must include at least one of:
- new unit test
- integration/regression update

---

## 한국어

## 테스트 피라미드(현재)

- 단위 테스트: 그래프/런타임/노드 동작
- 통합 테스트: 내구 큐 재전송, 그래프 E2E 동작
- 회귀 테스트: v2 골든 출력 비교

## 활성 테스트 위치

- 단위: `tests/unit/`
- 통합: `tests/integration/`
- 회귀: `tests/regression/`

## 기본 검증 명령

- 컴파일 게이트: `python3 -m compileall -q src tests scripts`
- pytest 게이트(환경 준비 시):
  - `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`

## 신뢰성 스모크(P24)

- quick 모드:
  - `python3 scripts/reliability_smoke.py --mode quick --json`
- full 모드:
  - `python3 scripts/reliability_smoke.py --mode full`

quick 모드는 durable 신뢰성 핵심 회귀에 집중한다:
- `tests/unit/test_sqlite_queue.py`
- `tests/unit/nodes/test_durable_sqlite_nodes.py`
- `tests/integration/test_durable_queue_replay.py`
- `tests/integration/test_durable_queue_reliability.py`

full 모드는 quick 범위에 아래를 추가한다:
- `tests/integration/test_v2_durable_queue_idempotency_e2e.py`

## 정책

런타임 동작 변경 시 아래 중 최소 하나를 포함해야 한다:
- 신규 단위 테스트
- 통합/회귀 테스트 업데이트
