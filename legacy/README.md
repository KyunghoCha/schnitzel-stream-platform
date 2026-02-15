# Legacy Archive

Last updated: 2026-02-15

## English

This directory is an isolated archive for legacy artifacts.
It is not part of the active runtime/source boundary.

## What Lives Here

- Legacy documentation archive: `legacy/docs/archive/`
- Legacy historical runtime docs: `legacy/docs/legacy/`
- Legacy helper scripts: `legacy/scripts/`

## What Does Not Live Here Anymore

- Legacy runtime source (`legacy/ai/**`) is removed from `main`.
- Compatibility shim (`src/ai/**`) is removed from tracked source.

## Active SSOT References

- Execution status SSOT: `docs/roadmap/execution_roadmap.md`
- Doc/code boundary mapping: `docs/reference/doc_code_mapping.md`

## Policy

- Do not add new production features under `legacy/`.
- If a historical artifact is needed, archive it under `legacy/docs/archive/`.

---

## 한국어

이 디렉터리는 레거시 아티팩트를 격리 보관하는 아카이브다.
Active 런타임/소스 경계에 포함되지 않는다.

## 포함 대상

- 레거시 문서 아카이브: `legacy/docs/archive/`
- 레거시 런타임 역사 문서: `legacy/docs/legacy/`
- 레거시 보조 스크립트: `legacy/scripts/`

## 더 이상 포함하지 않는 항목

- 레거시 런타임 소스(`legacy/ai/**`)는 `main`에서 제거됨
- 호환 shim(`src/ai/**`)은 추적 소스에서 제거됨

## Active SSOT 참조

- 실행 상태 SSOT: `docs/roadmap/execution_roadmap.md`
- 문서/코드 경계 매핑: `docs/reference/doc_code_mapping.md`

## 정책

- `legacy/` 아래에 신규 운영 기능을 추가하지 않는다.
- 역사 아티팩트가 필요하면 `legacy/docs/archive/`에 보관한다.
