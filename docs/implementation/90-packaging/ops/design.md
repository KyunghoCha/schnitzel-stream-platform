# Ops Packaging - Design

Last updated: 2026-02-15

## English

Purpose
-------

- Harden Phase 9.2 operating conventions so deployments are reproducible across Linux/Windows/macOS.

Key Decisions
-------------

- Keep `python -m schnitzel_stream` as the single runtime entry command for all lanes.
- Standardize path classes (`config`, `state`, `logs`) per OS to reduce operator ambiguity.
- Make no-Docker lane the portability baseline; Docker is an additional ops lane, not a prerequisite.
- Keep service-manager integration OS-native instead of introducing mandatory external daemons.

Service Strategy by OS
----------------------

| OS | Preferred service manager | Reason |
|---|---|---|
| Linux | `systemd` | Most common edge/server baseline; explicit restart policy and journald integration |
| Windows | Task Scheduler (or org-standard service wrapper) | Works without extra runtime dependency; common enterprise baseline |
| macOS | `launchd` | Native daemon model with plist-managed restart behavior |

Runtime Contract
----------------

- Command: `python -m schnitzel_stream --graph <graph.yaml>`
- Working directory: repo root (or deployment root with equivalent config paths)
- Environment: explicit file/profile (`PYTHONPATH=src` for source lane)
- Restart policy: always/on-failure with bounded restart delay

Failure Model
-------------

- Process crash: recovered by OS service manager restart.
- Plugin/network failures: handled in-node by retry/backoff policies (e.g., RTSP/HTTP sinks).
- Durable replay: handled by SQLite queue plugins when used in graph.

Operational Tradeoffs
---------------------

- Native service managers improve operability but require per-OS runbook snippets.
- no-Docker lane maximizes portability but depends on Python env hygiene.
- Docker lane simplifies dependency closure on Linux but is not universal on all edges.

Code Mapping
------------

- CLI entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Runtime graph engine: `src/schnitzel_stream/runtime/inproc.py`
- Durable queue nodes: `src/schnitzel_stream/nodes/durable_sqlite.py`
- Ops run commands: `docs/ops/command_reference.md`

## 한국어

목적
----

- Linux/Windows/macOS에서 재현 가능한 운영을 위해 Phase 9.2 운영 규약을 강화한다.

핵심 결정
---------

- 모든 레인에서 런타임 진입 명령을 `python -m schnitzel_stream`로 통일한다.
- 운영자 혼선을 줄이기 위해 OS별 경로 클래스(`config`, `state`, `logs`)를 표준화한다.
- 이식성 기준은 no-Docker 레인으로 두고, Docker는 추가 운영 레인으로 취급한다.
- 강제 외부 데몬을 도입하지 않고 OS 네이티브 서비스 관리자를 사용한다.

OS별 서비스 전략
-----------------

| OS | 권장 서비스 관리자 | 이유 |
|---|---|---|
| Linux | `systemd` | 가장 일반적인 엣지/서버 기준, 재시작 정책과 journald 연동 명확 |
| Windows | 작업 스케줄러(또는 조직 표준 서비스 래퍼) | 추가 런타임 의존성 없이 운영 가능, 엔터프라이즈 환경에서 보편적 |
| macOS | `launchd` | plist 기반 네이티브 데몬 모델 |

런타임 계약
-----------

- 명령: `python -m schnitzel_stream --graph <graph.yaml>`
- 작업 디렉터리: repo root(또는 동등한 설정 경로를 가진 배포 루트)
- 환경: 명시적 파일/프로파일(`source` 레인에서는 `PYTHONPATH=src`)
- 재시작 정책: always/on-failure + bounded restart delay

장애 모델
---------

- 프로세스 크래시: OS 서비스 관리자 재시작으로 복구.
- 플러그인/네트워크 장애: 노드 내부 retry/backoff 정책으로 처리(RTSP/HTTP sink 등).
- Durable 재전송: 그래프에서 SQLite queue 플러그인 사용 시 처리.

운영 트레이드오프
-----------------

- 네이티브 서비스 관리자 사용은 운영성을 높이지만, OS별 런북 스니펫 관리가 필요하다.
- no-Docker 레인은 이식성이 높지만 Python 환경 관리 품질에 민감하다.
- Docker 레인은 Linux 의존성 봉쇄에 유리하지만 모든 엣지에서 보편적이지 않다.

코드 매핑
---------

- CLI 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 런타임 그래프 엔진: `src/schnitzel_stream/runtime/inproc.py`
- Durable 큐 노드: `src/schnitzel_stream/nodes/durable_sqlite.py`
- 운영 실행 명령: `docs/ops/command_reference.md`
