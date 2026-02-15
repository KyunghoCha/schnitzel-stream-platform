# Doc-Code Mapping

Last updated: 2026-02-15

## English

This document is the active mapping between runtime code and maintained docs.

## Core Platform Mapping

| Capability | Code | Tests | Primary Docs |
|---|---|---|---|
| CLI entrypoint and command dispatch | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| Graph spec loading (v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| Graph validation (topology + compat) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| In-proc scheduler/runtime | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| Plugin loading policy | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| Packet contract | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Payload reference strategy | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Durable queue and replay primitives | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/integration/test_durable_queue_replay.py` | `docs/implementation/operations_release.md` |
| HTTP sink | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File sinks | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event nodes | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| Runtime throttle hook | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| Local mock backend tool | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| Runtime graphs/configs | `configs/graphs/*.yaml`, `configs/default.yaml` | graph validation and integration tests | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md` |

## Script Mapping

| Script | Purpose | Docs |
|---|---|---|
| `scripts/check_rtsp.py` | RTSP reconnect E2E smoke on v2 graph | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 golden comparison helper | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/multi_cam.py` | multi-process launcher helper | `docs/ops/command_reference.md` |

## Archive Boundary

Historical CCTV/legacy implementation docs are moved to `docs/archive/` and `docs/legacy/`.
They are not normative for active runtime behavior.

---

## 한국어

이 문서는 현재 유지되는 코드-문서 매핑 SSOT 입니다.

## 코어 플랫폼 매핑

| 기능 | 코드 | 테스트 | 주 문서 |
|---|---|---|---|
| CLI 엔트리포인트/명령 분기 | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| 그래프 스펙 로딩(v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| 그래프 검증(토폴로지 + 호환성) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| 인프로세스 런타임 스케줄러 | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| 플러그인 로딩 정책 | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| 패킷 계약 | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| payload_ref 전략 | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| 내구 큐/재전송 프리미티브 | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/integration/test_durable_queue_replay.py` | `docs/implementation/operations_release.md` |
| HTTP 싱크 | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File 싱크 | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event 노드 | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| 런타임 스로틀 훅 | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| 로컬 mock backend 도구 | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| 런타임 그래프/설정 | `configs/graphs/*.yaml`, `configs/default.yaml` | 그래프 검증/통합 테스트 | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md` |

## 스크립트 매핑

| 스크립트 | 목적 | 문서 |
|---|---|---|
| `scripts/check_rtsp.py` | v2 그래프 기반 RTSP 재연결 E2E 스모크 | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 골든 비교 헬퍼 | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/multi_cam.py` | 멀티 프로세스 런처 헬퍼 | `docs/ops/command_reference.md` |

## 아카이브 경계

역사적 CCTV/legacy 구현 문서는 `docs/archive/`, `docs/legacy/`로 이동했다.
현재 런타임 동작의 규범 문서로 사용하지 않는다.
