# Lab RC Release Checklist

Last updated: 2026-02-18

## English

## Purpose

This checklist defines the Lab RC release baseline for `v0.1.0-rc.1`.

- target: internal lab release candidate (not public beta)
- freeze scope: core + ops command surfaces only
- non-scope: research-track features (`R*`, `G*`), distributed control plane, runtime semantics changes

## Checklist

1. SSOT sync
- `docs/roadmap/execution_roadmap.md`
- `docs/progress/current_status.md`
- `PROMPT.md`
- `PROMPT_CORE.md`
- `docs/roadmap/owner_split_playbook.md`

2. Quality gates
- `python3 -m compileall -q src tests scripts`
- `python3 scripts/docs_hygiene.py --strict`
- `python3 scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0`

3. Runtime/reliability gates
- `python3 scripts/reliability_smoke.py --mode quick --json`
- `python3 scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml`

4. Drift gates
- `python3 scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json`
- `python3 scripts/command_surface_snapshot.py --check --baseline configs/policy/command_surface_snapshot_v1.json`
- `python3 scripts/ssot_sync_check.py --strict --json`

5. Conda reproducibility lane (required)
- `conda env update -n schnitzel-stream -f environment.yml --prune`
- `conda run -n schnitzel-stream python scripts/env_doctor.py --profile console --strict --json`
- `conda run -n schnitzel-stream python scripts/stream_run.py --preset inproc_demo --validate-only`

6. Release readiness aggregate
- `python3 scripts/release_readiness.py --profile lab-rc --json`

7. Tagging and note draft
- tag format: `v0.1.0-rc.1`
- include:
  - freeze scope
  - required gate summary
  - known limits (research track out of scope)

## 한국어

## 목적

이 체크리스트는 `v0.1.0-rc.1` 기준의 Lab RC 릴리즈 기준선을 정의한다.

- 타깃: 내부 연구실 릴리즈 후보(Lab RC, 공개 베타 아님)
- 동결 범위: core + ops 명령 표면
- 비범위: 연구 트랙(`R*`, `G*`), 분산 컨트롤 플레인, 런타임 의미론 변경

## 체크리스트

1. SSOT 동기화
- `docs/roadmap/execution_roadmap.md`
- `docs/progress/current_status.md`
- `PROMPT.md`
- `PROMPT_CORE.md`
- `docs/roadmap/owner_split_playbook.md`

2. 품질 게이트
- `python3 -m compileall -q src tests scripts`
- `python3 scripts/docs_hygiene.py --strict`
- `python3 scripts/test_hygiene.py --strict --max-duplicate-groups 0 --max-no-assert 0 --max-trivial-assert-true 0`

3. 런타임/신뢰성 게이트
- `python3 scripts/reliability_smoke.py --mode quick --json`
- `python3 scripts/proc_graph_validate.py --spec configs/process_graphs/dev_durable_pair_pg_v1.yaml`

4. 드리프트 게이트
- `python3 scripts/control_policy_snapshot.py --check --baseline configs/policy/control_api_policy_snapshot_v1.json`
- `python3 scripts/command_surface_snapshot.py --check --baseline configs/policy/command_surface_snapshot_v1.json`
- `python3 scripts/ssot_sync_check.py --strict --json`

5. conda 재현성 레인(required)
- `conda env update -n schnitzel-stream -f environment.yml --prune`
- `conda run -n schnitzel-stream python scripts/env_doctor.py --profile console --strict --json`
- `conda run -n schnitzel-stream python scripts/stream_run.py --preset inproc_demo --validate-only`

6. 릴리즈 준비 집약 명령
- `python3 scripts/release_readiness.py --profile lab-rc --json`

7. 태그/노트 초안
- 태그 형식: `v0.1.0-rc.1`
- 포함 항목:
  - 동결 범위
  - required 게이트 요약
  - 알려진 한계(연구 트랙 비범위)
