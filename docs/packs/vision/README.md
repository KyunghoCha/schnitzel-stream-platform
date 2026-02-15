# Vision Pack (CCTV lineage, optional)

Last updated: 2026-02-15

## English

This folder contains **vision/CCTV-adjacent** documentation that is intentionally kept **out of the platform core**.

Intent:
- Keep `schnitzel_stream` core domain-neutral (contracts/runtime/packaging).
- Keep vision-specific schemas and model adapter contracts versioned, but isolated as an optional "pack".

What lives here:

- Event schema/protocol: `docs/packs/vision/event_protocol_v0.2.md`
- Model adapter interface: `docs/packs/vision/model_interface.md`
- Class taxonomy (draft): `docs/packs/vision/model_class_taxonomy.md`
- I/O samples: `docs/packs/vision/model_io_samples.md`
- Ops/Training docs: `docs/packs/vision/ops/ai/`
- Code namespace: `src/schnitzel_stream/packs/vision/` (plugins: `schnitzel_stream.packs.vision.nodes:*`)

Related:

- Legacy pipeline runtime spec: `docs/legacy/specs/legacy_pipeline_spec.md` (v1 job graph)
- Platform contract: `docs/contracts/stream_packet.md`

---

## 한국어

이 폴더는 **비전/CCTV 계열** 문서를 담고 있으며, 의도적으로 **플랫폼 코어 밖**에 둡니다.

의도(Intent):
- `schnitzel_stream` 코어를 도메인 중립(계약/런타임/패키징)으로 유지합니다.
- 비전 전용 스키마/모델 어댑터 계약은 버전 관리하되, 옵션 "팩(pack)"으로 격리합니다.

포함 내용:

- 이벤트 스키마/프로토콜: `docs/packs/vision/event_protocol_v0.2.md`
- 모델 어댑터 인터페이스: `docs/packs/vision/model_interface.md`
- 클래스 분류(초안): `docs/packs/vision/model_class_taxonomy.md`
- 입출력 샘플: `docs/packs/vision/model_io_samples.md`
- 운영/학습 문서: `docs/packs/vision/ops/ai/`
- 코드 네임스페이스: `src/schnitzel_stream/packs/vision/` (플러그인: `schnitzel_stream.packs.vision.nodes:*`)

관련 문서:

- 레거시 파이프라인 런타임 스펙: `docs/legacy/specs/legacy_pipeline_spec.md` (v1 job graph)
- 플랫폼 코어 계약: `docs/contracts/stream_packet.md`
