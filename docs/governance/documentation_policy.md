# Documentation Policy

Last updated: 2026-02-15

## English

## Purpose

Define a maintainable documentation system for `schnitzel-stream-platform` so docs and code evolve together.

## Document Types

| Type | Goal | Update Rule | Location |
|---|---|---|---|
| SSOT | Normative decisions and contracts | Must be updated in the same PR as behavior changes | `docs/roadmap/`, `docs/contracts/`, `docs/design/` |
| Reference | Accurate mapping/indexes | Update whenever paths or ownership change | `docs/reference/` |
| Implementation | How current runtime is built | Update with architecture/runtime changes | `docs/implementation/` |
| Guides/Ops | Task-oriented usage | Update when CLI/config/workflow changes | `docs/guides/`, `docs/ops/`, `docs/packs/*` |
| Archive | Historical record only | No functional guarantees; do not use as SSOT | `docs/archive/`, `docs/legacy/` |

## Lifecycle States

- `active`: used for current development and operations
- `historical`: kept for context only
- `deprecated`: should not be used for new work

Rule:
- `active` docs must not reference deleted code paths.

## Authoring Rules

- Bilingual order: `## English` first, then `## 한국어`.
- One primary owner doc per concern (avoid duplicated SSOT).
- Include concrete file paths for code mapping.
- Prefer short, durable docs over speculative large docs.

## PR Rules (Docs-as-Code)

For PRs that change runtime behavior:
1. update at least one SSOT/reference doc in the same PR
2. update `docs/reference/doc_code_mapping.md` when paths/ownership change
3. move obsolete docs to `docs/archive/` instead of silently leaving stale content

## Change Control

- `docs/roadmap/execution_roadmap.md` is execution status SSOT.
- `docs/reference/doc_code_mapping.md` is code-to-doc map SSOT.

---

## 한국어

## 목적

`docs`와 코드가 함께 진화하도록, 유지 가능한 문서 관리 체계를 정의한다.

## 문서 타입

| 타입 | 목적 | 갱신 규칙 | 위치 |
|---|---|---|---|
| SSOT | 규범적 결정/계약 | 동작 변경 PR과 같은 PR에서 반드시 갱신 | `docs/roadmap/`, `docs/contracts/`, `docs/design/` |
| Reference | 정확한 매핑/인덱스 | 경로/소유권 변경 시 즉시 갱신 | `docs/reference/` |
| Implementation | 현재 런타임 구현 구조 | 아키텍처/런타임 변경 시 갱신 | `docs/implementation/` |
| Guides/Ops | 작업 중심 사용법 | CLI/설정/운영 워크플로우 변경 시 갱신 | `docs/guides/`, `docs/ops/`, `docs/packs/*` |
| Archive | 역사 기록 | 기능 보장 없음, SSOT로 사용 금지 | `docs/archive/`, `docs/legacy/` |

## 라이프사이클 상태

- `active`: 현재 개발/운영에서 사용
- `historical`: 맥락 참고용
- `deprecated`: 신규 작업에서 사용 금지

규칙:
- `active` 문서에는 삭제된 코드 경로를 남기지 않는다.

## 작성 규칙

- 이중언어 순서: `## English` 먼저, `## 한국어` 다음.
- 하나의 관심사에 하나의 주 문서(SSOT)만 둔다.
- 코드 매핑은 실제 파일 경로를 명시한다.
- 추측성 대문서보다 짧고 유지 가능한 문서를 우선한다.

## PR 규칙 (Docs-as-Code)

런타임 동작을 변경하는 PR은 다음을 따른다:
1. 같은 PR에서 SSOT/reference 문서를 최소 1개 이상 갱신
2. 경로/소유권이 바뀌면 `docs/reference/doc_code_mapping.md` 갱신
3. 오래된 문서는 방치하지 말고 `docs/archive/`로 이동

## 변경 통제

- 실행 상태 SSOT: `docs/roadmap/execution_roadmap.md`
- 코드-문서 매핑 SSOT: `docs/reference/doc_code_mapping.md`
