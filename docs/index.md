# Schnitzel Stream Docs Index

Last updated: 2026-02-15

## English

This directory is the documentation entrypoint for `schnitzel-stream-platform`.

Runtime baseline:
- Entrypoint: `python -m schnitzel_stream`
- Graph format: v2 node graph only (`version: 2`)
- Legacy v1 runtime (`ai.*`) removed from `main`

## Start Here

1. `docs/roadmap/execution_roadmap.md`
2. `docs/contracts/stream_packet.md`
3. `docs/contracts/observability.md`
4. `docs/design/architecture_2.0.md`
5. `docs/reference/doc_code_mapping.md`
6. `docs/ops/command_reference.md`

## Active Folders

- `docs/governance/`: documentation policy and lifecycle rules
- `docs/reference/`: doc inventory and code mapping
- `docs/roadmap/`: strategic/execution planning
- `docs/contracts/`: runtime contracts (packet/observability)
- `docs/design/`: architecture-level design
- `docs/implementation/`: active implementation notes (v2 runtime)
- `docs/ops/`: command and operations references
- `docs/guides/`: usage guides
- `docs/packs/`: pack-specific docs (vision etc.)
- `docs/progress/`: current status snapshots

## Historical Folders

- `docs/archive/`: archived implementation/ops/progress docs
- `docs/legacy/`: legacy runtime historical docs

## Code Mapping Entrypoints

- Runtime: `src/schnitzel_stream/runtime/inproc.py`
- Graph: `src/schnitzel_stream/graph/`
- CLI: `src/schnitzel_stream/cli/__main__.py`
- Plugins: `src/schnitzel_stream/plugins/registry.py`
- Pack nodes: `src/schnitzel_stream/packs/`

---

## 한국어

이 디렉터리는 `schnitzel-stream-platform` 문서의 진입점이다.

현재 런타임 기준:
- 엔트리포인트: `python -m schnitzel_stream`
- 그래프 포맷: v2 노드 그래프만 지원(`version: 2`)
- 레거시 v1 런타임(`ai.*`)은 `main`에서 제거됨

## 시작 순서

1. `docs/roadmap/execution_roadmap.md`
2. `docs/contracts/stream_packet.md`
3. `docs/contracts/observability.md`
4. `docs/design/architecture_2.0.md`
5. `docs/reference/doc_code_mapping.md`
6. `docs/ops/command_reference.md`

## 활성 폴더

- `docs/governance/`: 문서 정책/수명주기 규칙
- `docs/reference/`: 문서 인벤토리/코드 매핑
- `docs/roadmap/`: 전략/실행 계획
- `docs/contracts/`: 런타임 계약(packet/observability)
- `docs/design/`: 아키텍처 설계
- `docs/implementation/`: 활성 구현 노트(v2 런타임)
- `docs/ops/`: 명령어/운영 레퍼런스
- `docs/guides/`: 사용 가이드
- `docs/packs/`: 팩별 문서(vision 등)
- `docs/progress/`: 현재 상태 스냅샷

## 역사 폴더

- `docs/archive/`: 아카이브 구현/운영/진행 문서
- `docs/legacy/`: 레거시 런타임 역사 문서

## 코드 매핑 진입점

- 런타임: `src/schnitzel_stream/runtime/inproc.py`
- 그래프: `src/schnitzel_stream/graph/`
- CLI: `src/schnitzel_stream/cli/__main__.py`
- 플러그인: `src/schnitzel_stream/plugins/registry.py`
- 팩 노드: `src/schnitzel_stream/packs/`
