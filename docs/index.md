# Schnitzel Stream Docs Index

## English

This folder is the documentation SSOT for `schnitzel-stream-platform`.

Runtime baseline:
- Entrypoint: `python -m schnitzel_stream`
- Graph format: v2 node graph only (`version: 2`)
- Legacy v1 runtime (`ai.*`) was removed from `main`

### Start Here (Recommended Order)

1. `roadmap/strategic_roadmap.md`
2. `roadmap/execution_roadmap.md`
3. `contracts/stream_packet.md`
4. `contracts/observability.md`
5. `design/architecture_2.0.md`
6. `guides/v2_node_graph_guide.md`

### SSOT Pointers

- Execution plan/status: `roadmap/execution_roadmap.md`
- Packet contract: `contracts/stream_packet.md`
- Observability contract: `contracts/observability.md`
- Vision event contract: `packs/vision/event_protocol_v0.2.md`

### Folders

- `contracts/`: schema/protocol contracts
- `design/`: architecture/design specs
- `guides/`: practical usage guides
- `ops/`: deployment/operations references
- `packs/`: optional domain packs (vision, sensors, etc)
- `roadmap/`: strategy + execution roadmap
- `progress/`: progress and validation logs
- `legacy/`: historical docs kept for reference only

### Code Mapping

- CLI entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Graph loader: `src/schnitzel_stream/graph/spec.py`
- Runtime engine: `src/schnitzel_stream/runtime/inproc.py`
- Plugin registry/policy: `src/schnitzel_stream/plugins/registry.py`
- Default graph: `configs/graphs/dev_vision_e2e_mock_v2.yaml`

## 한국어

이 폴더는 `schnitzel-stream-platform` 문서 SSOT 입니다.

현재 런타임 기준:
- 엔트리포인트: `python -m schnitzel_stream`
- 그래프 포맷: v2 노드 그래프만 지원 (`version: 2`)
- 레거시 v1 런타임(`ai.*`)은 `main`에서 제거됨

### 시작 순서 (권장)

1. `roadmap/strategic_roadmap.md`
2. `roadmap/execution_roadmap.md`
3. `contracts/stream_packet.md`
4. `contracts/observability.md`
5. `design/architecture_2.0.md`
6. `guides/v2_node_graph_guide.md`

### SSOT 포인터

- 실행 계획/상태: `roadmap/execution_roadmap.md`
- 패킷 계약: `contracts/stream_packet.md`
- 관측 가능성 계약: `contracts/observability.md`
- 비전 이벤트 계약: `packs/vision/event_protocol_v0.2.md`

### 폴더 안내

- `contracts/`: 스키마/프로토콜 계약
- `design/`: 아키텍처/설계 명세
- `guides/`: 실전 가이드
- `ops/`: 배포/운영 레퍼런스
- `packs/`: 옵션 도메인 팩(vision, sensors 등)
- `roadmap/`: 전략 + 실행 로드맵
- `progress/`: 진행/검증 로그
- `legacy/`: 참고용 역사 문서

### 코드 매핑

- CLI 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 그래프 로더: `src/schnitzel_stream/graph/spec.py`
- 런타임 엔진: `src/schnitzel_stream/runtime/inproc.py`
- 플러그인 레지스트리/정책: `src/schnitzel_stream/plugins/registry.py`
- 기본 그래프: `configs/graphs/dev_vision_e2e_mock_v2.yaml`
