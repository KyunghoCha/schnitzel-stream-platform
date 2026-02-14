# Legacy Decommission (P4.1 SSOT)

Last updated: 2026-02-14

목표: `legacy/ai/**` 레거시 런타임(import 경로: `ai.*`)과 v1(job) 그래프 포맷을 **계획적으로 제거**하고, v2(node) 그래프 기반 플랫폼으로 완전히 전환한다.

이 문서는 Phase 4(`P4.*`)의 기준 문서이며, “언제/무엇을 기준으로 레거시를 없애는가”를 정의한다.

## What Counts As “Legacy”

- 코드: `legacy/ai/**` (+ `src/ai` shim)
- v1(job) 그래프 포맷: `version: 1`
- 레거시 그래프(v1): `configs/graphs/legacy_pipeline.yaml`
- Phase 0 호환 job: `src/schnitzel_stream/jobs/legacy_ai_pipeline.py`
- 플러그인 allowlist에 포함된 `ai.*` 네임스페이스

## Strategy (Strangler, No Big Bang)

1. **Define parity** (`P4.1`): 어떤 동작을 “같다”고 볼지, 무엇을 버릴지 명확히 한다.
2. **Reach parity with v2** (`P4.2`): v2 그래프 + 노드로 운영에 필요한 행동을 커버한다.
   - 필요하면 “래핑”을 허용하되, 래핑은 임시이며 최종 목표는 `ai.*` 의존성 제거다.
3. **Cutover** (`P4.3`): 기본 그래프를 v2로 바꾸고 v1을 deprecate 한다.
4. **Extract or quarantine** (`P4.4`): 레거시를 별도 패키지/리포/`legacy/`로 고정해 남기거나, 내부 전용으로 격리한다.
5. **Delete** (`P4.5`): deprecation window 종료 후 main tree에서 제거한다.

## Parity Scope (Baseline)

레거시 기능을 전부 복제하는 것이 아니라, “운영에 필요한 최소”를 먼저 정의한다.

Baseline 후보(조정 가능):
- 입력: 파일/RTSP/Webcam 중 최소 1개는 v2로 제공
- 처리: 샘플링/전처리/모델 추론/후처리(추적/퓨전)/정책(Zone/Dedup)/이벤트 빌드
- 출력: backend/file/stdout 중 최소 1개 sink를 v2로 제공
- 장애/재시작: `at-least-once + idempotency` 기반의 replay 가능성(Phase 2 durable queue 사용 가능)
- 관측: `docs/contracts/observability.md` 수준의 metrics/health 일관성

명시적으로 “초기엔 안 한다” 후보:
- GUI 시각화(디버그 window)
- 멀티 센서 퓨전의 모든 모드
- 모든 모델/백엔드 조합

## Cutover Criteria (Definition of Done)

`P4.3`(default v2 전환) 기준:
- v2 그래프가 **운영 baseline**을 커버한다(위 Parity Scope 합의 버전).
- 최소 1개의 end-to-end “golden” 시나리오가 자동화 테스트로 존재한다.
- v1(job) 실행은 유지하되, 문서와 CLI에서 deprecation이 명시된다.

`P4.5`(legacy 삭제) 기준:
- `P4.3`가 **머지된 이후 최소 90일**이 지났다. (deprecation window)
- `main` 기준으로 `schnitzel_stream.*`에서 `ai.*` 직접 import가 0이다.
- v1 그래프를 사용하는 내부/외부 소비자가 없다(또는 `P4.4`로 별도 패키지로 격리/이관됨).

## Deprecation Policy (Timeline)

- 레거시 삭제는 **절대 즉시 삭제하지 않는다**.
- `P4.3` 머지 시점에 이 문서와 `docs/roadmap/execution_roadmap.md`에 “절대 날짜”를 기록한다.

현재 기록:
- v1 deprecation 시작일: **2026-02-14**
- `legacy/ai/**` 제거 가능 최단일: **2026-05-15** (>= 90 days after `P4.3`)

## Operational Policy (Until Removed)

- `legacy/ai/**`는 “기능 추가 금지(Freeze)”가 기본이다.
  - 허용: 보안/크래시/데이터 손실 버그 픽스
  - 금지: 신규 기능/새 플러그인 경계 확장/새 설정 키 추가

## Open Questions

- Baseline parity에서 “모델 추론”을 어디까지 포함할지(ONNX/YOLO/Custom)
- backend event schema의 고정 범위(필수 필드/optional 필드)
- multi-camera/multi-sensor를 Phase 4에 포함할지, 이후로 미룰지
