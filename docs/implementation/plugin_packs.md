# Plugin Packs and Extension Boundaries

Last updated: 2026-02-15

## English

## Boundary Rules

- Core runtime must stay domain-neutral.
- Domain behavior should live in plugin packs.
- Default plugin allowlist is `schnitzel_stream.*`.

## Active Namespaces

- Core nodes: `src/schnitzel_stream/nodes/`
- Vision pack: `src/schnitzel_stream/packs/vision/`
- Policy modules: `src/schnitzel_stream/policy/`
- Plugin registry policy: `src/schnitzel_stream/plugins/registry.py`

## Plugin Path Convention

- Format: `module:ClassName`
- Example:
  - `schnitzel_stream.packs.vision.nodes:OpenCvRtspSource`
  - `schnitzel_stream.nodes.http:HttpJsonSink`

## Operational Rule

When adding/changing plugins:
1. update code
2. add/adjust unit tests
3. update docs in `docs/ops/command_reference.md` and `docs/reference/doc_code_mapping.md`

---

## 한국어

## 경계 규칙

- 코어 런타임은 도메인 중립을 유지해야 한다.
- 도메인 동작은 플러그인 팩으로 분리한다.
- 기본 플러그인 allowlist는 `schnitzel_stream.*`이다.

## 활성 네임스페이스

- 코어 노드: `src/schnitzel_stream/nodes/`
- 비전 팩: `src/schnitzel_stream/packs/vision/`
- 정책 모듈: `src/schnitzel_stream/policy/`
- 플러그인 정책: `src/schnitzel_stream/plugins/registry.py`

## 플러그인 경로 규약

- 형식: `module:ClassName`
- 예시:
  - `schnitzel_stream.packs.vision.nodes:OpenCvRtspSource`
  - `schnitzel_stream.nodes.http:HttpJsonSink`

## 운영 규칙

플러그인을 추가/변경할 때:
1. 코드 변경
2. 단위 테스트 추가/수정
3. `docs/ops/command_reference.md`, `docs/reference/doc_code_mapping.md` 갱신
