# Schnitzel Stream Docs Index

Last updated: 2026-02-19

## English

This directory is the documentation entrypoint for `schnitzel-stream-platform`.

Runtime baseline:
- Entrypoint: `python -m schnitzel_stream`
- Graph format: v2 node graph only (`version: 2`)
- Legacy v1 runtime (`ai.*`) removed from `main`

## Start Here

1. `docs/roadmap/execution_roadmap.md`
2. `docs/roadmap/owner_split_playbook.md`
3. `docs/roadmap/strategic_roadmap.md`
4. `docs/roadmap/future_backlog.md`
5. `docs/reference/document_inventory.md`
6. `docs/reference/doc_code_mapping.md`
7. `docs/progress/README.md`
8. `docs/progress/current_status.md`
9. `docs/contracts/stream_packet.md`
10. `docs/contracts/observability.md`
11. `docs/design/architecture_2.0.md`
12. `docs/design/future_structure.md`
13. `docs/ops/command_reference.md`
14. `docs/guides/plugin_authoring_guide.md`
15. `docs/guides/process_graph_foundation_guide.md`
16. `docs/guides/professor_showcase_guide.md`
17. `docs/guides/local_console_quickstart.md`
18. `docs/guides/graph_wizard_guide.md`
19. `docs/guides/block_editor_quickstart.md`
20. `docs/guides/lab_rc_release_checklist.md`
21. `docs/experiments/backpressure_fairness_paper_plan.md`

Onboarding standard path:
- `bootstrap -> doctor -> up/down`
- `docs/guides/local_console_quickstart.md`

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
- `docs/experiments/`: reproducible experiment and paper plans

## Historical Docs

- Legacy docs were removed from the working tree on 2026-02-16.
- Use git history/tag for historical lookup: `pre-legacy-purge-20260216`.

## Code Mapping Entrypoints

- Runtime: `src/schnitzel_stream/runtime/inproc.py`
- Graph: `src/schnitzel_stream/graph/`
- Process graph (foundation): `src/schnitzel_stream/procgraph/`
- CLI: `src/schnitzel_stream/cli/__main__.py`
- Plugins: `src/schnitzel_stream/plugins/registry.py`
- Pack nodes: `src/schnitzel_stream/packs/`
- Fleet runner: `scripts/stream_fleet.py`
- Stream monitor: `scripts/stream_monitor.py`
- Preset launcher (no-env-first): `scripts/stream_run.py`
- Graph wizard (template-profile graph generator): `scripts/graph_wizard.py`
- Plugin scaffold + contract check: `scripts/scaffold_plugin.py`, `scripts/plugin_contract_check.py`
- Dependency bootstrap helper: `scripts/bootstrap_env.py`, `environment.yml`
- Stream console bootstrap: `scripts/stream_console.py`
- Stream control API: `scripts/stream_control_api.py`, `src/schnitzel_stream/control_api/`
- Graph editor ops service: `src/schnitzel_stream/ops/graph_editor.py`
- Block editor direct-manipulation UI: `apps/stream-console/src/App.tsx`, `apps/stream-console/src/editor_nodes.tsx`, `apps/stream-console/src/editor_layout.ts`, `apps/stream-console/src/editor_connect.ts`
- Control policy snapshot gate: `scripts/control_policy_snapshot.py`, `configs/policy/control_api_policy_snapshot_v1.json`
- Command surface snapshot gate: `scripts/command_surface_snapshot.py`, `configs/policy/command_surface_snapshot_v1.json`
- SSOT sync drift gate: `scripts/ssot_sync_check.py`, `configs/policy/ssot_sync_snapshot_v1.json`
- Release readiness aggregate gate: `scripts/release_readiness.py`
- Environment diagnostics: `scripts/env_doctor.py`
- Reliability smoke gate: `scripts/reliability_smoke.py`
- Showcase report renderer: `scripts/demo_report_view.py`
- Web console: `apps/stream-console/`

---

## 한국어

이 디렉터리는 `schnitzel-stream-platform` 문서의 진입점이다.

현재 런타임 기준:
- 엔트리포인트: `python -m schnitzel_stream`
- 그래프 포맷: v2 노드 그래프만 지원(`version: 2`)
- 레거시 v1 런타임(`ai.*`)은 `main`에서 제거됨

## 시작 순서

1. `docs/roadmap/execution_roadmap.md`
2. `docs/roadmap/owner_split_playbook.md`
3. `docs/roadmap/strategic_roadmap.md`
4. `docs/roadmap/future_backlog.md`
5. `docs/reference/document_inventory.md`
6. `docs/reference/doc_code_mapping.md`
7. `docs/progress/README.md`
8. `docs/progress/current_status.md`
9. `docs/contracts/stream_packet.md`
10. `docs/contracts/observability.md`
11. `docs/design/architecture_2.0.md`
12. `docs/design/future_structure.md`
13. `docs/ops/command_reference.md`
14. `docs/guides/plugin_authoring_guide.md`
15. `docs/guides/process_graph_foundation_guide.md`
16. `docs/guides/professor_showcase_guide.md`
17. `docs/guides/local_console_quickstart.md`
18. `docs/guides/graph_wizard_guide.md`
19. `docs/guides/block_editor_quickstart.md`
20. `docs/guides/lab_rc_release_checklist.md`
21. `docs/experiments/backpressure_fairness_paper_plan.md`

온보딩 표준 경로:
- `bootstrap -> doctor -> up/down`
- `docs/guides/local_console_quickstart.md`

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
- `docs/experiments/`: 재현 실험/논문 계획

## 역사 문서

- 레거시 문서는 2026-02-16에 워킹 트리에서 제거됨.
- 과거 문서는 git 이력/태그(`pre-legacy-purge-20260216`)에서 조회.

## 코드 매핑 진입점

- 런타임: `src/schnitzel_stream/runtime/inproc.py`
- 그래프: `src/schnitzel_stream/graph/`
- 프로세스 그래프(foundation): `src/schnitzel_stream/procgraph/`
- CLI: `src/schnitzel_stream/cli/__main__.py`
- 플러그인: `src/schnitzel_stream/plugins/registry.py`
- 팩 노드: `src/schnitzel_stream/packs/`
- Fleet 실행기: `scripts/stream_fleet.py`
- Stream 모니터: `scripts/stream_monitor.py`
- 프리셋 실행기(무환경변수 우선): `scripts/stream_run.py`
- Graph wizard(템플릿 프로필 그래프 생성기): `scripts/graph_wizard.py`
- 플러그인 스캐폴드 + 계약 검사: `scripts/scaffold_plugin.py`, `scripts/plugin_contract_check.py`
- 의존성 부트스트랩 헬퍼: `scripts/bootstrap_env.py`, `environment.yml`
- Stream 콘솔 부트스트랩: `scripts/stream_console.py`
- Stream Control API: `scripts/stream_control_api.py`, `src/schnitzel_stream/control_api/`
- 그래프 편집 ops 서비스: `src/schnitzel_stream/ops/graph_editor.py`
- 블록 에디터 직접 조작 UI: `apps/stream-console/src/App.tsx`, `apps/stream-console/src/editor_nodes.tsx`, `apps/stream-console/src/editor_layout.ts`, `apps/stream-console/src/editor_connect.ts`
- 제어 정책 스냅샷 게이트: `scripts/control_policy_snapshot.py`, `configs/policy/control_api_policy_snapshot_v1.json`
- 명령 표면 스냅샷 게이트: `scripts/command_surface_snapshot.py`, `configs/policy/command_surface_snapshot_v1.json`
- SSOT 동기화 드리프트 게이트: `scripts/ssot_sync_check.py`, `configs/policy/ssot_sync_snapshot_v1.json`
- 릴리즈 준비 집약 게이트: `scripts/release_readiness.py`
- 환경 진단: `scripts/env_doctor.py`
- 신뢰성 스모크 게이트: `scripts/reliability_smoke.py`
- 쇼케이스 리포트 렌더러: `scripts/demo_report_view.py`
- 웹 콘솔: `apps/stream-console/`
