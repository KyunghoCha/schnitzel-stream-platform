# Ops Packaging - Spec

Last updated: 2026-02-15

## English

Behavior
--------

- Define OS-specific service-mode conventions for long-running edge deployments.
- Keep runtime invocation consistent across OSes: `python -m schnitzel_stream --graph <path>`.
- Treat Docker as optional; no-Docker lane remains first-class.

Path Conventions
----------------

| OS | Config | State/Queue/Outputs | Logs |
|---|---|---|---|
| Linux | `/etc/schnitzel-stream/` | `/var/lib/schnitzel-stream/` | `/var/log/schnitzel-stream/` |
| Windows | `%ProgramData%\\SchnitzelStream\\config\\` | `%ProgramData%\\SchnitzelStream\\state\\` | `%ProgramData%\\SchnitzelStream\\logs\\` |
| macOS | `/usr/local/etc/schnitzel-stream/` | `/usr/local/var/lib/schnitzel-stream/` | `/usr/local/var/log/schnitzel-stream/` |

Service Mode Requirements
-------------------------

- Service process must auto-restart on failure.
- Service process should run with least privilege (non-root where possible).
- Service definitions must set explicit working directory and environment file/source.
- Stop behavior should allow graceful shutdown (SIGTERM/CTRL_BREAK equivalent) before hard kill.

Logging Requirements
--------------------

- Primary process logs must be collectible from the OS service manager and/or configured log path.
- Runtime-generated artifacts (JSONL, snapshots, file sinks) must write to explicit writable paths.
- Sensitive values in URLs must be masked in logs.

Config
------

- no-Docker lane uses venv + `PYTHONPATH=src`.
- Service command should pin graph path explicitly instead of relying on defaults.

Status
------

- P9.2 conventions are documented and linked from command reference.

Code Mapping
------------

- Entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Command reference: `docs/ops/command_reference.md`
- Packaging matrix: `docs/implementation/90-packaging/support_matrix.md`

## 한국어

동작
----

- 장기 실행 엣지 배포를 위한 OS별 서비스 모드 규약을 정의한다.
- OS가 달라도 실행 명령을 일관되게 유지한다: `python -m schnitzel_stream --graph <path>`.
- Docker는 선택이며, no-Docker 레인을 1급 경로로 유지한다.

경로 규약
---------

| OS | 설정 | 상태/큐/출력 | 로그 |
|---|---|---|---|
| Linux | `/etc/schnitzel-stream/` | `/var/lib/schnitzel-stream/` | `/var/log/schnitzel-stream/` |
| Windows | `%ProgramData%\\SchnitzelStream\\config\\` | `%ProgramData%\\SchnitzelStream\\state\\` | `%ProgramData%\\SchnitzelStream\\logs\\` |
| macOS | `/usr/local/etc/schnitzel-stream/` | `/usr/local/var/lib/schnitzel-stream/` | `/usr/local/var/log/schnitzel-stream/` |

서비스 모드 요구사항
--------------------

- 장애 시 자동 재시작 정책을 가져야 한다.
- 가능하면 최소 권한(비루트)으로 실행한다.
- 서비스 정의에 작업 디렉터리와 환경 파일/환경 소스를 명시한다.
- 종료 시 즉시 강제 종료하지 않고 graceful shutdown(SIGTERM/CTRL_BREAK 등) 기회를 먼저 제공한다.

로그 요구사항
-------------

- 주 프로세스 로그는 OS 서비스 관리자 또는 지정 로그 경로에서 수집 가능해야 한다.
- 런타임 산출물(JSONL/스냅샷/파일 sink)은 명시적 writable 경로에 저장해야 한다.
- URL 내 민감정보는 로그에서 마스킹되어야 한다.

설정
----

- no-Docker 레인은 venv + `PYTHONPATH=src`를 사용한다.
- 서비스 명령은 기본값 의존 대신 그래프 경로를 명시한다.

상태
----

- P9.2 규약 문서화 완료, 명령어 레퍼런스와 연동됨.

코드 매핑
---------

- 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 명령어 레퍼런스: `docs/ops/command_reference.md`
- 패키징 매트릭스: `docs/implementation/90-packaging/support_matrix.md`
