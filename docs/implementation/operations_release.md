# Operations and Release Implementation

Last updated: 2026-02-19

## English

## Runtime/Ops Surfaces

Frozen Core+Ops command surfaces for Lab RC:
- `python -m schnitzel_stream`
- `python scripts/stream_run.py`
- `python scripts/stream_fleet.py`
- `python scripts/stream_monitor.py`
- `python scripts/stream_console.py`
- `python scripts/env_doctor.py`
- `python scripts/graph_wizard.py`
- `python scripts/stream_control_api.py`

Runtime semantics freeze:
- in-proc scheduler semantics unchanged
- v2 node-graph + process-graph foundation contracts unchanged

## Lab RC Baseline

- Release target: internal Lab RC (`v0.1.0-rc.1`)
- Scope: productization closure for implementation track (research track excluded)
- Non-scope: `R*`/`G*`, distributed control-plane runtime, semantic redesign

## Required Gates (pip + conda)

Pip lane (`no-docker-smoke`) required checks:
- compile/docs/test hygiene
- reliability smoke (`quick`)
- policy drift gate (`control_policy_snapshot`)
- surface drift gate (`command_surface_snapshot`)
- SSOT drift gate (`ssot_sync_check --strict`)

Conda lane (`conda-smoke`) required checks:
- `env_doctor --profile console --strict --json`
- compile check
- `stream_run --preset inproc_demo --validate-only`
- policy/surface/SSOT drift gates

Aggregate local check:
- `python3 scripts/release_readiness.py --profile lab-rc --json`

## Drift Baseline Update Procedure

When intentional changes happen in frozen surfaces:
1. update implementation
2. regenerate/update baseline file in same change set
3. re-run drift checks
4. document reason in PR/release note

Baseline files:
- `configs/policy/control_api_policy_snapshot_v1.json`
- `configs/policy/command_surface_snapshot_v1.json`
- `configs/policy/ssot_sync_snapshot_v1.json`

## Tagging and Notes

Tag workflow:
1. all required gates green
2. create annotated tag `v0.1.0-rc.1`
3. attach release notes including:
- freeze scope
- required gate summary
- known limits (`R*`/`G*` out of scope)

Checklist reference:
- `docs/guides/lab_rc_release_checklist.md`

---

## 한국어

## 런타임/운영 표면

Lab RC에서 동결하는 Core+Ops 명령 표면:
- `python -m schnitzel_stream`
- `python scripts/stream_run.py`
- `python scripts/stream_fleet.py`
- `python scripts/stream_monitor.py`
- `python scripts/stream_console.py`
- `python scripts/env_doctor.py`
- `python scripts/graph_wizard.py`
- `python scripts/stream_control_api.py`

런타임 의미론 동결:
- in-proc 스케줄러 의미론 유지
- v2 노드 그래프 + process-graph foundation 계약 유지

## Lab RC 기준선

- 릴리즈 타깃: 내부 Lab RC (`v0.1.0-rc.1`)
- 범위: 구현 트랙 제품화 마감(연구 트랙 제외)
- 비범위: `R*`/`G*`, 분산 컨트롤 플레인 런타임, 의미론 재설계

## Required 게이트 (pip + conda)

pip 레인(`no-docker-smoke`) 필수 항목:
- compile/docs/test hygiene
- 신뢰성 스모크(`quick`)
- 정책 드리프트 게이트(`control_policy_snapshot`)
- 명령면 드리프트 게이트(`command_surface_snapshot`)
- SSOT 드리프트 게이트(`ssot_sync_check --strict`)

conda 레인(`conda-smoke`) 필수 항목:
- `env_doctor --profile console --strict --json`
- compile 검사
- `stream_run --preset inproc_demo --validate-only`
- 정책/명령면/SSOT 드리프트 게이트

로컬 집약 검사:
- `python3 scripts/release_readiness.py --profile lab-rc --json`

## 드리프트 baseline 갱신 절차

동결 표면을 의도적으로 변경할 때:
1. 구현 변경
2. 같은 변경셋에서 baseline 파일 갱신
3. 드리프트 체크 재실행
4. PR/릴리즈 노트에 변경 이유 기록

baseline 파일:
- `configs/policy/control_api_policy_snapshot_v1.json`
- `configs/policy/command_surface_snapshot_v1.json`
- `configs/policy/ssot_sync_snapshot_v1.json`

## 태깅/노트

태그 절차:
1. required 게이트 전체 green 확인
2. `v0.1.0-rc.1` annotated tag 생성
3. 릴리즈 노트에 다음 포함:
- 동결 범위
- required 게이트 요약
- 알려진 한계(`R*`/`G*` 비범위)

체크리스트 문서:
- `docs/guides/lab_rc_release_checklist.md`
