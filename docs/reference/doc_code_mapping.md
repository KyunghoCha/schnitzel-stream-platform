# Doc-Code Mapping

Last updated: 2026-02-19

## English

This document is the active mapping between runtime code and maintained docs.

## Active vs Legacy Boundary

| Scope | Active (Normative) | Legacy (Historical Only) | Rule |
|---|---|---|---|
| Documentation | `docs/**` | none (in-tree) | Historical docs are preserved via git history/tag (`pre-legacy-purge-20260216`). |
| Scripts | `scripts/**` | none (in-tree) | Only `scripts/**` are active helper scripts for the current platform runtime. |
| Runtime Code | `src/schnitzel_stream/**` | none | Legacy runtime code is not part of active tracked source roots. |
| Frontend Console | `apps/stream-console/**` | none | Web console is a thin UI over control API contracts. |
| Runtime Config | `configs/**` | none | Historical behavior/config intent is preserved in git history/tag. |

## Core Platform Mapping

| Capability | Code | Tests | Primary Docs |
|---|---|---|---|
| Ownership split and research gate contract | `N/A (docs policy artifact)` | `python3 scripts/docs_hygiene.py --strict` | `docs/roadmap/owner_split_playbook.md`, `docs/roadmap/execution_roadmap.md`, `docs/progress/current_status.md` |
| Future target structure blueprint | `N/A (docs design artifact)` | `python3 scripts/docs_hygiene.py --strict` | `docs/design/future_structure.md`, `docs/roadmap/future_backlog.md`, `docs/roadmap/owner_split_playbook.md` |
| CLI entrypoint and command dispatch | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| Graph spec loading (v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| Process-graph spec loading (v1 foundation) | `src/schnitzel_stream/procgraph/spec.py`, `src/schnitzel_stream/procgraph/model.py` | `tests/unit/procgraph/test_proc_graph_spec.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/implementation/runtime_core.md` |
| Graph validation (topology + compat) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py`, `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| Process-graph validation (sqlite bridge, strict 1:1) | `src/schnitzel_stream/procgraph/validate.py` | `tests/unit/procgraph/test_proc_graph_validate.py`, `tests/unit/scripts/test_proc_graph_validate_script.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/design/architecture_2.0.md` |
| In-proc scheduler/runtime | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| Plugin loading policy | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| Plugin DX scaffold and contract checks | `scripts/scaffold_plugin.py`, `scripts/plugin_contract_check.py` | `tests/unit/scripts/test_scaffold_plugin.py`, `tests/unit/scripts/test_plugin_contract_check.py` | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| Packet contract | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Payload reference strategy | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| Durable queue and replay primitives | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/unit/nodes/test_durable_sqlite_nodes.py`, `tests/integration/test_durable_queue_replay.py`, `tests/integration/test_durable_queue_reliability.py` | `docs/implementation/operations_release.md`, `docs/implementation/testing_quality.md` |
| HTTP sink | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File sinks | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event nodes | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| Runtime throttle hook | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| Payload profile contract | `src/schnitzel_stream/contracts/payload_profile.py` | `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| Local mock backend tool | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| Ops shared service layer (preset/fleet/monitor/env/console) | `src/schnitzel_stream/ops/*.py` | `tests/unit/scripts/test_stream_run.py`, `tests/unit/scripts/test_stream_fleet.py`, `tests/unit/scripts/test_stream_monitor.py`, `tests/unit/scripts/test_env_doctor.py`, `tests/unit/ops/test_console_ops.py` | `docs/ops/command_reference.md`, `README.md`, `docs/guides/local_console_quickstart.md` |
| Stream control API + governance hardening | `src/schnitzel_stream/control_api/*.py`, `scripts/stream_control_api.py`, `scripts/control_policy_snapshot.py`, `configs/policy/control_api_policy_snapshot_v1.json` | `tests/unit/control_api/test_control_api.py`, `tests/unit/control_api/test_audit.py`, `tests/unit/scripts/test_control_policy_snapshot.py` | `docs/ops/command_reference.md`, `README.md`, `docs/roadmap/execution_roadmap.md` |
| Productization drift gates (Lab RC freeze) | `scripts/command_surface_snapshot.py`, `scripts/ssot_sync_check.py`, `scripts/release_readiness.py`, `configs/policy/command_surface_snapshot_v1.json`, `configs/policy/ssot_sync_snapshot_v1.json` | `tests/unit/scripts/test_command_surface_snapshot.py`, `tests/unit/scripts/test_ssot_sync_check.py`, `tests/unit/scripts/test_release_readiness.py` | `docs/guides/lab_rc_release_checklist.md`, `docs/implementation/operations_release.md`, `docs/ops/command_reference.md` |
| Stream console web UI | `apps/stream-console/src/*.tsx`, `apps/stream-console/src/*.ts` | `apps/stream-console/src/App.test.tsx` | `README.md`, `docs/ops/command_reference.md` |
| Graph authoring wizard (template profiles) | `scripts/graph_wizard.py`, `src/schnitzel_stream/ops/graph_wizard.py`, `configs/wizard_profiles/*.yaml`, `configs/graphs/templates/*.yaml` | `tests/unit/ops/test_graph_wizard_ops.py`, `tests/unit/scripts/test_graph_wizard.py` | `docs/guides/graph_wizard_guide.md`, `docs/ops/command_reference.md`, `README.md` |
| Dependency baseline bootstrap (Conda + pip) | `environment.yml`, `scripts/bootstrap_env.py`, `setup_env.ps1`, `setup_env.sh` | `python3 scripts/bootstrap_env.py --profile base --manager pip --dry-run --skip-doctor --json` | `README.md`, `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md` |
| Block editor ops + API bridge | `src/schnitzel_stream/ops/graph_editor.py`, `src/schnitzel_stream/control_api/app.py`, `src/schnitzel_stream/control_api/models.py`, `apps/stream-console/src/App.tsx`, `apps/stream-console/src/api.ts`, `apps/stream-console/src/editor_nodes.tsx`, `apps/stream-console/src/editor_layout.ts`, `apps/stream-console/src/editor_connect.ts` | `tests/unit/ops/test_graph_editor_ops.py`, `tests/unit/control_api/test_control_api.py`, `apps/stream-console/src/App.test.tsx`, `apps/stream-console/src/editor_layout.test.ts`, `apps/stream-console/src/editor_connect.test.ts` | `docs/guides/block_editor_quickstart.md`, `docs/ops/command_reference.md`, `README.md` |
| Runtime graphs/configs | `configs/graphs/*.yaml`, `configs/process_graphs/*.yaml`, `configs/default.yaml`, `configs/fleet.yaml` | graph validation and integration tests | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md`, `docs/guides/process_graph_foundation_guide.md`, `docs/guides/professor_showcase_guide.md` |

## Script Mapping

| Script | Purpose | Docs |
|---|---|---|
| `scripts/env_doctor.py` | runtime environment/dependency diagnostics (`--strict`, `--json`, `--profile`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/check_rtsp.py` | RTSP reconnect E2E smoke on v2 graph | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 golden comparison helper | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/reliability_smoke.py` | durable reliability smoke gate (`quick`/`full`, JSON summary contract) | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/stream_fleet.py` | generic stream fleet launcher (`start`/`stop`/`status`) | `docs/ops/command_reference.md` |
| `scripts/stream_monitor.py` | read-only stream TUI monitor (pid/log based) | `docs/ops/command_reference.md` |
| `scripts/stream_run.py` | one-command preset launcher (`--list`, `--preset`, `--experimental`, `--doctor`, YOLO override flags) | `docs/ops/command_reference.md`, `README.md`, `docs/guides/local_console_quickstart.md` |
| `scripts/graph_wizard.py` | non-interactive template-profile graph generator (`--list-profiles`, `--profile --out`, `--validate --spec`) | `docs/guides/graph_wizard_guide.md`, `docs/ops/command_reference.md`, `README.md` |
| `scripts/bootstrap_env.py` | dependency bootstrap helper (`--profile`, `--manager`, `--env-name`, `--dry-run`, `--skip-doctor`, `--json`) | `README.md`, `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md` |
| `scripts/stream_console.py` | one-command local console bootstrap (`up`/`status`/`down`/`doctor`) | `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md`, `README.md` |
| `scripts/stream_control_api.py` | local-first control API server (optional bearer auth + governance endpoints) | `docs/ops/command_reference.md`, `README.md` |
| `scripts/control_policy_snapshot.py` | control policy snapshot emit/check (`--check` drift gate) | `docs/ops/command_reference.md`, `README.md` |
| `scripts/command_surface_snapshot.py` | frozen command surface snapshot emit/check (`--check` drift gate) | `docs/ops/command_reference.md`, `docs/guides/lab_rc_release_checklist.md` |
| `scripts/ssot_sync_check.py` | SSOT step/status synchronization drift checker (`--strict`, `--json`) | `docs/ops/command_reference.md`, `docs/roadmap/execution_roadmap.md` |
| `scripts/release_readiness.py` | aggregated Lab RC release gate runner (`--profile lab-rc`, `--json`) | `docs/guides/lab_rc_release_checklist.md`, `docs/implementation/operations_release.md`, `docs/ops/command_reference.md` |
| `scripts/proc_graph_validate.py` | process-graph foundation validator (`version: 1`) | `docs/ops/command_reference.md`, `docs/guides/process_graph_foundation_guide.md` |
| `scripts/scaffold_plugin.py` | plugin code/test/graph scaffold generator (`--dry-run`, `--validate-generated`) | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| `scripts/plugin_contract_check.py` | plugin pack/module/graph contract checker (`--strict`, `--json`) | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| `scripts/demo_pack.py` | one-command showcase runner (`ci` / `professor`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/demo_report_view.py` | static showcase report renderer (Markdown/HTML) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
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
| 프론트엔드 콘솔 | `apps/stream-console/**` | 없음 | 웹 콘솔은 control API 계약 위에서 동작하는 thin UI다. |
| 런타임 설정 | `configs/**` | 없음 | 과거 동작/설정 의도는 git 이력/태그로 보존한다. |

## 코어 플랫폼 매핑

| 기능 | 코드 | 테스트 | 주 문서 |
|---|---|---|---|
| 소유권 분리/연구 게이트 계약 | `N/A (문서 정책 산출물)` | `python3 scripts/docs_hygiene.py --strict` | `docs/roadmap/owner_split_playbook.md`, `docs/roadmap/execution_roadmap.md`, `docs/progress/current_status.md` |
| 미래 목표 구조 블루프린트 | `N/A (문서 설계 산출물)` | `python3 scripts/docs_hygiene.py --strict` | `docs/design/future_structure.md`, `docs/roadmap/future_backlog.md`, `docs/roadmap/owner_split_playbook.md` |
| CLI 엔트리포인트/명령 분기 | `src/schnitzel_stream/__main__.py`, `src/schnitzel_stream/cli/__main__.py` | `tests/unit/test_cli_validate_only.py` | `docs/ops/command_reference.md`, `docs/implementation/runtime_core.md` |
| 그래프 스펙 로딩(v2) | `src/schnitzel_stream/graph/spec.py` | `tests/unit/test_node_graph_spec.py` | `docs/implementation/runtime_core.md` |
| 프로세스 그래프 스펙 로딩(v1 foundation) | `src/schnitzel_stream/procgraph/spec.py`, `src/schnitzel_stream/procgraph/model.py` | `tests/unit/procgraph/test_proc_graph_spec.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/implementation/runtime_core.md` |
| 그래프 검증(토폴로지 + 호환성) | `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py` | `tests/unit/test_graph_validate.py`, `tests/unit/test_graph_compat.py`, `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| 프로세스 그래프 검증(SQLite 브리지, strict 1:1) | `src/schnitzel_stream/procgraph/validate.py` | `tests/unit/procgraph/test_proc_graph_validate.py`, `tests/unit/scripts/test_proc_graph_validate_script.py` | `docs/guides/process_graph_foundation_guide.md`, `docs/design/architecture_2.0.md` |
| 인프로세스 런타임 스케줄러 | `src/schnitzel_stream/runtime/inproc.py` | `tests/unit/test_inproc_*.py` | `docs/implementation/runtime_core.md` |
| 플러그인 로딩 정책 | `src/schnitzel_stream/plugins/registry.py` | `tests/unit/test_graph_compat.py` | `docs/implementation/plugin_packs.md` |
| 플러그인 DX 스캐폴드/계약 검사 | `scripts/scaffold_plugin.py`, `scripts/plugin_contract_check.py` | `tests/unit/scripts/test_scaffold_plugin.py`, `tests/unit/scripts/test_plugin_contract_check.py` | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| 패킷 계약 | `src/schnitzel_stream/packet.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| payload_ref 전략 | `src/schnitzel_stream/nodes/blob_ref.py` | `tests/unit/test_payload_ref_roundtrip.py` | `docs/contracts/stream_packet.md` |
| 내구 큐/재전송 프리미티브 | `src/schnitzel_stream/nodes/durable_sqlite.py`, `src/schnitzel_stream/state/sqlite_queue.py` | `tests/unit/test_sqlite_queue.py`, `tests/unit/nodes/test_durable_sqlite_nodes.py`, `tests/integration/test_durable_queue_replay.py`, `tests/integration/test_durable_queue_reliability.py` | `docs/implementation/operations_release.md`, `docs/implementation/testing_quality.md` |
| HTTP 싱크 | `src/schnitzel_stream/nodes/http.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| JSONL/File 싱크 | `src/schnitzel_stream/nodes/file_sink.py` | `tests/unit/nodes/test_file_sink_nodes.py` | `docs/ops/command_reference.md` |
| Vision source/policy/event 노드 | `src/schnitzel_stream/packs/vision/nodes/*.py`, `src/schnitzel_stream/packs/vision/policy/*.py` | `tests/unit/nodes/test_video_nodes.py`, `tests/unit/nodes/test_policy_nodes.py`, `tests/unit/nodes/test_event_builder_node.py` | `docs/packs/vision/README.md`, `docs/packs/vision/event_protocol_v0.2.md`, `docs/packs/vision/model_interface.md` |
| 런타임 스로틀 훅 | `src/schnitzel_stream/control/throttle.py` | `tests/unit/test_inproc_throttle.py` | `docs/contracts/observability.md`, `docs/implementation/runtime_core.md` |
| payload profile 계약 | `src/schnitzel_stream/contracts/payload_profile.py` | `tests/unit/test_payload_profile.py` | `docs/contracts/stream_packet.md`, `docs/implementation/runtime_core.md` |
| 로컬 mock backend 도구 | `src/schnitzel_stream/tools/mock_backend.py` | `tests/unit/nodes/test_http_nodes.py` | `docs/ops/command_reference.md` |
| Ops 공통 서비스 레이어(preset/fleet/monitor/env/console) | `src/schnitzel_stream/ops/*.py` | `tests/unit/scripts/test_stream_run.py`, `tests/unit/scripts/test_stream_fleet.py`, `tests/unit/scripts/test_stream_monitor.py`, `tests/unit/scripts/test_env_doctor.py`, `tests/unit/ops/test_console_ops.py` | `docs/ops/command_reference.md`, `README.md`, `docs/guides/local_console_quickstart.md` |
| Stream control API + 거버넌스 하드닝 | `src/schnitzel_stream/control_api/*.py`, `scripts/stream_control_api.py`, `scripts/control_policy_snapshot.py`, `configs/policy/control_api_policy_snapshot_v1.json` | `tests/unit/control_api/test_control_api.py`, `tests/unit/control_api/test_audit.py`, `tests/unit/scripts/test_control_policy_snapshot.py` | `docs/ops/command_reference.md`, `README.md`, `docs/roadmap/execution_roadmap.md` |
| 제품화 드리프트 게이트(Lab RC 동결) | `scripts/command_surface_snapshot.py`, `scripts/ssot_sync_check.py`, `scripts/release_readiness.py`, `configs/policy/command_surface_snapshot_v1.json`, `configs/policy/ssot_sync_snapshot_v1.json` | `tests/unit/scripts/test_command_surface_snapshot.py`, `tests/unit/scripts/test_ssot_sync_check.py`, `tests/unit/scripts/test_release_readiness.py` | `docs/guides/lab_rc_release_checklist.md`, `docs/implementation/operations_release.md`, `docs/ops/command_reference.md` |
| Stream console 웹 UI | `apps/stream-console/src/*.tsx`, `apps/stream-console/src/*.ts` | `apps/stream-console/src/App.test.tsx` | `README.md`, `docs/ops/command_reference.md` |
| 그래프 작성 wizard(템플릿 프로필) | `scripts/graph_wizard.py`, `src/schnitzel_stream/ops/graph_wizard.py`, `configs/wizard_profiles/*.yaml`, `configs/graphs/templates/*.yaml` | `tests/unit/ops/test_graph_wizard_ops.py`, `tests/unit/scripts/test_graph_wizard.py` | `docs/guides/graph_wizard_guide.md`, `docs/ops/command_reference.md`, `README.md` |
| 의존성 기준선 부트스트랩(Conda + pip) | `environment.yml`, `scripts/bootstrap_env.py`, `setup_env.ps1`, `setup_env.sh` | `python3 scripts/bootstrap_env.py --profile base --manager pip --dry-run --skip-doctor --json` | `README.md`, `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md` |
| 블록 에디터 ops + API 브리지 | `src/schnitzel_stream/ops/graph_editor.py`, `src/schnitzel_stream/control_api/app.py`, `src/schnitzel_stream/control_api/models.py`, `apps/stream-console/src/App.tsx`, `apps/stream-console/src/api.ts`, `apps/stream-console/src/editor_nodes.tsx`, `apps/stream-console/src/editor_layout.ts`, `apps/stream-console/src/editor_connect.ts` | `tests/unit/ops/test_graph_editor_ops.py`, `tests/unit/control_api/test_control_api.py`, `apps/stream-console/src/App.test.tsx`, `apps/stream-console/src/editor_layout.test.ts`, `apps/stream-console/src/editor_connect.test.ts` | `docs/guides/block_editor_quickstart.md`, `docs/ops/command_reference.md`, `README.md` |
| 런타임 그래프/설정 | `configs/graphs/*.yaml`, `configs/process_graphs/*.yaml`, `configs/default.yaml`, `configs/fleet.yaml` | 그래프 검증/통합 테스트 | `docs/ops/command_reference.md`, `docs/guides/v2_node_graph_guide.md`, `docs/guides/process_graph_foundation_guide.md`, `docs/guides/professor_showcase_guide.md` |

## 스크립트 매핑

| 스크립트 | 목적 | 문서 |
|---|---|---|
| `scripts/env_doctor.py` | 런타임 환경/의존성 진단(`--strict`, `--json`, `--profile`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/check_rtsp.py` | v2 그래프 기반 RTSP 재연결 E2E 스모크 | `docs/ops/command_reference.md` |
| `scripts/regression_check.py` | v2 골든 비교 헬퍼 | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/reliability_smoke.py` | durable 신뢰성 스모크 게이트(`quick`/`full`, JSON 요약 계약) | `docs/ops/command_reference.md`, `docs/implementation/testing_quality.md` |
| `scripts/stream_fleet.py` | 범용 stream fleet 실행기(`start`/`stop`/`status`) | `docs/ops/command_reference.md` |
| `scripts/stream_monitor.py` | 읽기 전용 stream TUI 모니터(pid/log 기반) | `docs/ops/command_reference.md` |
| `scripts/stream_run.py` | 원커맨드 프리셋 실행기(`--list`, `--preset`, `--experimental`, `--doctor`, YOLO override 옵션) | `docs/ops/command_reference.md`, `README.md`, `docs/guides/local_console_quickstart.md` |
| `scripts/graph_wizard.py` | 비상호작용 템플릿 프로필 그래프 생성기(`--list-profiles`, `--profile --out`, `--validate --spec`) | `docs/guides/graph_wizard_guide.md`, `docs/ops/command_reference.md`, `README.md` |
| `scripts/bootstrap_env.py` | 의존성 부트스트랩 헬퍼(`--profile`, `--manager`, `--env-name`, `--dry-run`, `--skip-doctor`, `--json`) | `README.md`, `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md` |
| `scripts/stream_console.py` | 원커맨드 로컬 콘솔 부트스트랩(`up`/`status`/`down`/`doctor`) | `docs/ops/command_reference.md`, `docs/guides/local_console_quickstart.md`, `README.md` |
| `scripts/stream_control_api.py` | 로컬 우선 control API 서버(선택적 Bearer 인증 + 거버넌스 엔드포인트) | `docs/ops/command_reference.md`, `README.md` |
| `scripts/control_policy_snapshot.py` | 제어 정책 스냅샷 생성/검사(`--check` 드리프트 게이트) | `docs/ops/command_reference.md`, `README.md` |
| `scripts/command_surface_snapshot.py` | 동결 명령 표면 스냅샷 생성/검사(`--check` 드리프트 게이트) | `docs/ops/command_reference.md`, `docs/guides/lab_rc_release_checklist.md` |
| `scripts/ssot_sync_check.py` | SSOT step/status 동기화 드리프트 검사(`--strict`, `--json`) | `docs/ops/command_reference.md`, `docs/roadmap/execution_roadmap.md` |
| `scripts/release_readiness.py` | Lab RC 집약 릴리즈 게이트 실행기(`--profile lab-rc`, `--json`) | `docs/guides/lab_rc_release_checklist.md`, `docs/implementation/operations_release.md`, `docs/ops/command_reference.md` |
| `scripts/proc_graph_validate.py` | 프로세스 그래프 foundation 검증기(`version: 1`) | `docs/ops/command_reference.md`, `docs/guides/process_graph_foundation_guide.md` |
| `scripts/scaffold_plugin.py` | 플러그인 코드/테스트/그래프 스캐폴드 생성기(`--dry-run`, `--validate-generated`) | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| `scripts/plugin_contract_check.py` | 플러그인 팩/모듈/그래프 계약 검사기(`--strict`, `--json`) | `docs/guides/plugin_authoring_guide.md`, `docs/implementation/plugin_packs.md`, `docs/ops/command_reference.md` |
| `scripts/demo_pack.py` | 원커맨드 쇼케이스 실행기(`ci` / `professor`) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/demo_report_view.py` | 쇼케이스 리포트 정적 렌더러(Markdown/HTML) | `docs/ops/command_reference.md`, `docs/guides/professor_showcase_guide.md` |
| `scripts/docs_hygiene.py` | 문서 구조/참조 무결성 검사기 | `docs/governance/documentation_policy.md` |

## 아카이브 경계

역사적 CCTV/legacy 구현 문서는 워킹 트리에 두지 않는다.
조회가 필요하면 git 이력/태그 `pre-legacy-purge-20260216`를 사용한다.
