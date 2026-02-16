# Operations and Release Implementation

Last updated: 2026-02-16

## English

## Runtime/Ops Surfaces

- CLI and graph selection: `python -m schnitzel_stream --graph ...`
- Runtime configs: `configs/default.yaml`, `configs/graphs/*.yaml`
- Utility tooling: `scripts/check_rtsp.py`, `scripts/regression_check.py`, `scripts/stream_fleet.py`, `scripts/stream_monitor.py`
- Local HTTP sink target: `python -m schnitzel_stream.tools.mock_backend`

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

## 패키징 레인

- venv + pip 레인(주 no-docker 레인)
- 옵션 Docker 레인(배포 환경 의존)

## 운영 문서

- 명령어 레퍼런스: `docs/ops/command_reference.md`
- 지원/로드맵 맥락: `docs/roadmap/execution_roadmap.md`
