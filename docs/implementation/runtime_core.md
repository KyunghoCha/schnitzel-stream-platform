# Runtime Core Implementation

Last updated: 2026-02-16

## English

## Scope

Defines the active runtime core for `version: 2` node graphs.

## Code Mapping

- CLI entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Graph model/spec: `src/schnitzel_stream/graph/model.py`, `src/schnitzel_stream/graph/spec.py`
- Validation: `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py`
- Scheduler: `src/schnitzel_stream/runtime/inproc.py`
- Packet contract: `src/schnitzel_stream/packet.py`
- Node protocol: `src/schnitzel_stream/node.py`

## Execution Flow

1. Parse graph YAML (`version: 2` only).
2. Validate topology and compatibility.
3. Load plugins through `PluginRegistry`.
4. Run source iterators and route packets in-process.
5. Emit metrics/run report.

## Payload Profiles (P10.5 draft)

- Validator may use plugin-declared profiles:
  - `INPUT_PROFILE`
  - `OUTPUT_PROFILE`
- Supported values:
  - `inproc_any`
  - `json_portable`
  - `ref_portable`
- Backward compatibility:
  - plugins that still use `REQUIRES_PORTABLE_PAYLOAD` remain supported
  - validator bridges legacy flags to profile checks

## Non-goals (Current)

- distributed scheduler
- automatic control plane
- unrestricted cycle execution semantics

---

## 한국어

## 범위

`version: 2` 노드 그래프 기준 활성 런타임 코어를 정의한다.

## 코드 매핑

- CLI 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 그래프 모델/스펙: `src/schnitzel_stream/graph/model.py`, `src/schnitzel_stream/graph/spec.py`
- 검증기: `src/schnitzel_stream/graph/validate.py`, `src/schnitzel_stream/graph/compat.py`
- 스케줄러: `src/schnitzel_stream/runtime/inproc.py`
- 패킷 계약: `src/schnitzel_stream/packet.py`
- 노드 프로토콜: `src/schnitzel_stream/node.py`

## 실행 흐름

1. 그래프 YAML 파싱(`version: 2`만 지원)
2. 토폴로지/호환성 검증
3. `PluginRegistry`로 플러그인 로딩
4. source iterator 실행 및 in-proc 패킷 라우팅
5. 메트릭/실행 리포트 출력

## Payload Profile (P10.5 초안)

- Validator는 플러그인이 선언한 profile 속성을 사용할 수 있다:
  - `INPUT_PROFILE`
  - `OUTPUT_PROFILE`
- 지원 값:
  - `inproc_any`
  - `json_portable`
  - `ref_portable`
- 하위 호환:
  - 기존 `REQUIRES_PORTABLE_PAYLOAD` 기반 플러그인은 계속 지원
  - validator가 레거시 플래그를 profile 검증으로 브리지

## 현재 비범위

- 분산 스케줄러
- 자동 컨트롤 플레인
- 무제한 루프 그래프 실행 의미론
