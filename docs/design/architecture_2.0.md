# Architecture 2.0 (PROVISIONAL)

Last updated: 2026-02-16

## English

Intent:
- This document is provisional and tracks the current platform baseline.
- Baseline runtime is v2 node graph execution via `python -m schnitzel_stream`.

### Summary

- **Scope**: platform boundaries, runtime contracts, and extension points.
- **Non-scope**: distributed scheduler/control plane, final cycle runtime semantics.

### Boundary Map

- Platform core: `src/schnitzel_stream/`
  - CLI: `src/schnitzel_stream/cli/__main__.py`
  - Graph spec/validation: `src/schnitzel_stream/graph/`
  - Runtime scheduler: `src/schnitzel_stream/runtime/`
  - Plugin policy/registry: `src/schnitzel_stream/plugins/registry.py`
  - Contracts: `src/schnitzel_stream/packet.py`, `src/schnitzel_stream/node.py`
- Plugin packs: `src/schnitzel_stream/packs/`
  - Example: vision nodes/policy/event builders
- Historical docs are not kept in the working tree.
  - Legacy v1 runtime code is removed from `main` (history/tag: `pre-legacy-purge-20260216`).

### Runtime Contract

- Graph format: `version: 2`
- Node contract: `run()` for sources, `process(packet)` for nodes/sinks
- Packet contract: `StreamPacket`
- Validation:
  - topology checks (strict DAG by default)
  - static compatibility checks (kind/transport portability)

### Policy & Safety

- Default plugin allowlist: `schnitzel_stream.*`
- Optional dev override via env:
  - `ALLOWED_PLUGIN_PREFIXES`
  - `ALLOW_ALL_PLUGINS=true`

### Open Questions

- Cycle-capable runtime semantics (`R1`) and safe guardrails
- Cross-process/distributed transport boundary design
- Control-plane integration scope (`P3.3`, optional)

---

## 한국어

의도(Intent):
- 이 문서는 잠정 문서이며 현재 플랫폼 기준선을 추적합니다.
- 현재 기준 런타임은 `python -m schnitzel_stream` 기반 v2 노드 그래프 실행입니다.

### 요약

- **범위**: 플랫폼 경계, 런타임 계약, 확장 지점.
- **비범위**: 분산 스케줄러/컨트롤 플레인, 최종 루프 그래프 실행 의미론.

### 경계 맵

- 플랫폼 코어: `src/schnitzel_stream/`
  - CLI: `src/schnitzel_stream/cli/__main__.py`
  - 그래프 스펙/검증: `src/schnitzel_stream/graph/`
  - 런타임 스케줄러: `src/schnitzel_stream/runtime/`
  - 플러그인 정책/레지스트리: `src/schnitzel_stream/plugins/registry.py`
  - 계약: `src/schnitzel_stream/packet.py`, `src/schnitzel_stream/node.py`
- 플러그인 팩: `src/schnitzel_stream/packs/`
  - 예: vision 노드/정책/이벤트 빌더
- 참고용 역사 문서는 워킹 트리에 두지 않는다.
  - 레거시 v1 런타임 코드는 `main`에서 제거되었고, 이력은 태그(`pre-legacy-purge-20260216`)로 조회한다.

### 런타임 계약

- 그래프 포맷: `version: 2`
- 노드 계약: source는 `run()`, node/sink는 `process(packet)`
- 패킷 계약: `StreamPacket`
- 검증:
  - 토폴로지 검증(기본 strict DAG)
  - 정적 호환성 검증(kind/transport portability)

### 정책 & 안전

- 기본 플러그인 allowlist: `schnitzel_stream.*`
- 개발용 완화(env):
  - `ALLOWED_PLUGIN_PREFIXES`
  - `ALLOW_ALL_PLUGINS=true`

### 미해결 질문

- 루프 가능 런타임 의미론(`R1`)과 안전 가드레일
- 프로세스/분산 경계에서의 transport 설계
- 컨트롤 플레인 통합 범위(`P3.3`, optional)
