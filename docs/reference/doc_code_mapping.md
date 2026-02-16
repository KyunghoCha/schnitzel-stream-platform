# Doc-Code Mapping

Last updated: 2026-02-16

## English

This document is the active mapping between runtime code and maintained docs.

## Active vs Legacy Boundary

| Scope | Active (Normative) | Legacy (Historical Only) | Rule |
|---|---|---|---|
| Documentation | `docs/**` | none (in-tree) | Historical docs are preserved via git history/tag (`pre-legacy-purge-20260216`). |
| Scripts | `scripts/**` | none (in-tree) | Only `scripts/**` are active helper scripts for the current platform runtime. |
| Runtime Code | `src/schnitzel_stream/**` | none | Legacy runtime code is not part of active tracked source roots. |
| Runtime Config | `configs/**` | none | Historical behavior/config intent is preserved in git history/tag. |

## Core Platform Mapping

| Capability | Code | Tests | Primary Docs |
|---|---|---|---|
| Ownership split and research gate contract | `N/A (docs policy artifact)` | `python3 scripts/docs_hygiene.py --strict` | `docs/roadmap/owner_split_playbook.md`, `docs/roadmap/execution_roadmap.md`, `docs/progress/current_status.md` |
| CLI entrypoint and command dispatch | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| Graph spec loading (v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| Process-graph spec loading (v1 foundation) | `src/schnitzel_stream/procgraph/spec.py`, `src/schnitzel_stream/procgraph/model.py` | `tests/unit/procgraph/test_proc_graph_spec.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/implementation/runtime_core.md` |
| Graph validation (topology + compat) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py`, `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| Process-graph validation (sqlite bridge, strict 1:1) | `src/schnitzel_stream/procgraph/validate.py` | `tests/unit/procgraph/test_proc_graph_validate.py`, `tests/unit/scripts/test_proc_graph_validate.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/design/architecture_2.0.md` |
| In-proc scheduler/runtime | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| Plugin loading policy | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| Packet contract | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Payload reference strategy | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Durable queue and replay primitives | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/integration/test_durable_queue_replay.py` | `docs/implementation/operations_release.md` |
| HTTP sink | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File sinks | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event nodes | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| Runtime throttle hook | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| Payload profile contract | `src/schnitzel_stream/contracts/payload_profile.py` | `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| Local mock backend tool | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| Runtime graphs/configs | `configs/graphs/*.yaml`, `configs/process_graphs/*.yaml`, `configs/default.yaml` | graph validation and integration tests | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md`, `docs/guides/process_graph_foundation_guide.md`, `docs/guides/professor_showcase_guide.md` |

## Script Mapping

| Script | Purpose | Docs |
|---|---|---|
| `scripts/check_rtsp.py` | RTSP reconnect E2E smoke on v2 graph | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 golden comparison helper | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/multi_cam.py` | camera-by-camera graph launcher helper | `docs/ops/command_reference.md` |
| `scripts/proc_graph_validate.py` | process-graph foundation validator (`version: 1`) | `docs/ops/command_reference.md`, `docs/guides/process_graph_foundation_guide.md` |
| `scripts/scaffold_plugin.py` | plugin code/test/graph scaffold generator | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md` |
| `scripts/demo_pack.py` | one-command showcase runner (`ci` / `professor`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/docs_hygiene.py` | docs structure/reference hygiene checker | `docs/governance/documentation_policy.md` |

## Archive Boundary

Historical CCTV/legacy implementation docs are not kept in the working tree.
Use git history/tag `pre-legacy-purge-20260216` for historical lookup.

---

## 한국어

이 문서는 현재 유지되는 코드-문서 매핑 SSOT 입니다.

## Active vs Legacy 경계

| 범위 | Active(규범) | Legacy(역사 보관용) | 규칙 |
|---|---|---|---|
| 문서 | `docs/**` | 없음(in-tree) | 역사 문서는 git 이력/태그(`pre-legacy-purge-20260216`)로 조회한다. |
| 스크립트 | `scripts/**` | 없음(in-tree) | 현재 플랫폼 런타임 헬퍼 스크립트는 `scripts/**`만 Active로 본다. |
| 런타임 코드 | `src/schnitzel_stream/**` | 없음 | 레거시 런타임 코드는 현재 추적 소스 루트에 포함하지 않는다. |
| 런타임 설정 | `configs/**` | 없음 | 과거 동작/설정 의도는 git 이력/태그로 보존한다. |

## 코어 플랫폼 매핑

| 기능 | 코드 | 테스트 | 주 문서 |
|---|---|---|---|
| 소유권 분리/연구 게이트 계약 | `N/A (문서 정책 산출물)` | `python3 scripts/docs_hygiene.py --strict` | `docs/roadmap/owner_split_playbook.md`, `docs/roadmap/execution_roadmap.md`, `docs/progress/current_status.md` |
| CLI 엔트리포인트/명령 분기 | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| 그래프 스펙 로딩(v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| 프로세스 그래프 스펙 로딩(v1 foundation) | `src/schnitzel_stream/procgraph/spec.py`, `src/schnitzel_stream/procgraph/model.py` | `tests/unit/procgraph/test_proc_graph_spec.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/implementation/runtime_core.md` |
| 그래프 검증(토폴로지 + 호환성) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py`, `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| 프로세스 그래프 검증(SQLite 브리지, strict 1:1) | `src/schnitzel_stream/procgraph/validate.py` | `tests/unit/procgraph/test_proc_graph_validate.py`, `tests/unit/scripts/test_proc_graph_validate.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/design/architecture_2.0.md` |
| 인프로세스 런타임 스케줄러 | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| 플러그인 로딩 정책 | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| 패킷 계약 | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| payload_ref 전략 | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| 내구 큐/재전송 프리미티브 | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/integration/test_durable_queue_replay.py` | `docs/implementation/operations_release.md` |
| HTTP 싱크 | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File 싱크 | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event 노드 | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| 런타임 스로틀 훅 | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| payload profile 계약 | `src/schnitzel_stream/contracts/payload_profile.py` | `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| 로컬 mock backend 도구 | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| 런타임 그래프/설정 | `configs/graphs/*.yaml`, `configs/process_graphs/*.yaml`, `configs/default.yaml` | 그래프 검증/통합 테스트 | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md`, `docs/guides/process_graph_foundation_guide.md`, `docs/guides/professor_showcase_guide.md` |

## 스크립트 매핑

| 스크립트 | 목적 | 문서 |
|---|---|---|
| `scripts/check_rtsp.py` | v2 그래프 기반 RTSP 재연결 E2E 스모크 | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 골든 비교 헬퍼 | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/multi_cam.py` | 카메라별 그래프 런처 헬퍼 | `docs/ops/command_reference.md` |
| `scripts/proc_graph_validate.py` | 프로세스 그래프 foundation 검증기(`version: 1`) | `docs/ops/command_reference.md`, `docs/guides/process_graph_foundation_guide.md` |
| `scripts/scaffold_plugin.py` | 플러그인 코드/테스트/그래프 스캐폴드 생성기 | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md` |
| `scripts/demo_pack.py` | 원커맨드 쇼케이스 실행기(`ci` / `professor`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/docs_hygiene.py` | 문서 구조/참조 무결성 검사기 | `docs/governance/documentation_policy.md` |

## 아카이브 경계

역사적 CCTV/legacy 구현 문서는 워킹 트리에 두지 않는다.
조회가 필요하면 git 이력/태그 `pre-legacy-purge-20260216`를 사용한다.
