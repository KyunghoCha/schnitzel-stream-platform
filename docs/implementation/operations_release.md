# Operations and Release Implementation

Last updated: 2026-02-18

## English

## Runtime/Ops Surfaces

- CLI and graph selection: `python -m schnitzel_stream --graph ...`
- Runtime configs: `configs/default.yaml`, `configs/graphs/*.yaml`
- Utility tooling: `scripts/check_rtsp.py`, `scripts/regression_check.py`, `scripts/stream_fleet.py`, `scripts/stream_monitor.py`
- Local HTTP sink target: `python -m schnitzel_stream.tools.mock_backend`

## Lab RC Baseline

- Release target: internal Lab RC (`v0.1.0-rc.1`)
- Freeze scope: Core+Ops command surfaces only
- Non-scope: research-track (`R*`, `G*`), distributed control-plane, runtime semantic changes

Tagging policy:
1. confirm release readiness gates
2. create annotated tag `v0.1.0-rc.1`
3. attach release notes with freeze scope + known limits

Checklist:
- `docs/guides/lab_rc_release_checklist.md`

## Packaging Lanes

- venv + pip lane (primary no-docker lane)
- optional Docker lane (deployment dependent)

## Ops Documentation

- command reference: `docs/ops/command_reference.md`
- support/roadmap context: `docs/roadmap/execution_roadmap.md`

---

## 한국어

## 런타임/운영 표면

- CLI/그래프 선택: `python -m schnitzel_stream --graph ...`
- 런타임 설정: `configs/default.yaml`, `configs/graphs/*.yaml`
- 유틸리티 도구: `scripts/check_rtsp.py`, `scripts/regression_check.py`, `scripts/stream_fleet.py`, `scripts/stream_monitor.py`
- 로컬 HTTP 싱크 타겟: `python -m schnitzel_stream.tools.mock_backend`

## Lab RC 기준선

- 릴리즈 타깃: 내부 Lab RC (`v0.1.0-rc.1`)
- 동결 범위: Core+Ops 명령 표면
- 비범위: 연구 트랙(`R*`, `G*`), 분산 컨트롤 플레인, 런타임 의미론 변경

태깅 정책:
1. 릴리즈 준비 게이트 통과 확인
2. `v0.1.0-rc.1` annotated tag 생성
3. 동결 범위/알려진 한계를 포함한 릴리즈 노트 작성

체크리스트:
- `docs/guides/lab_rc_release_checklist.md`

## 패키징 레인

- venv + pip 레인(주 no-docker 레인)
- 옵션 Docker 레인(배포 환경 의존)

## 운영 문서

- 명령어 레퍼런스: `docs/ops/command_reference.md`
- 지원/로드맵 맥락: `docs/roadmap/execution_roadmap.md`
