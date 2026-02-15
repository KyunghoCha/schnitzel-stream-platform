# Observability Contract v1 (PROVISIONAL)

## English

### Purpose

Define a minimal, stable observability contract (metrics + health) that works across runtimes/transports.

### Run Report JSON (v1)

When `--report-json` is enabled (currently: v2 in-proc runtime), the CLI prints **one JSON object** to stdout:

- `ts` (string): ISO-8601 timestamp (UTC recommended)
- `status` (string): `ok` | `degraded` | `error`
- `engine` (string): execution engine id (example: `inproc`)
- `graph_version` (int): graph spec version
- `graph` (string): graph spec path
- `metrics` (object): `string -> int` map

### Metric Naming (v1)

Baseline keys (runner-provided):

- `packets.consumed_total`
- `packets.produced_total`
- `packets.source_emitted_total`
- `packets.dropped_total` (inbox overflow, backpressure policy)
- `node.<node_id>.consumed`
- `node.<node_id>.produced`
- `node.<node_id>.is_source` (0|1)
- `node.<node_id>.is_sink` (0|1)
- `node.<node_id>.inbox_dropped_total` (inbox overflow, runner-enforced)

Extension keys (node-provided, optional):

- `node.<node_id>.<metric_name>` (int only; example: `node.queue.queue_depth`)

## 한국어

### 목적

런타임/전송 방식이 달라져도 공통으로 쓸 수 있는 최소 관측 가능성 계약(메트릭/헬스)을 정의합니다.

### 실행 리포트 JSON (v1)

`--report-json` 옵션이 켜져 있을 때(현재: v2 in-proc 런타임), CLI는 stdout에 **JSON 1개 객체**를 출력합니다:

- `ts` (string): ISO-8601 타임스탬프 (UTC 권장)
- `status` (string): `ok` | `degraded` | `error`
- `engine` (string): 실행 엔진 식별자 (예: `inproc`)
- `graph_version` (int): 그래프 스펙 버전
- `graph` (string): 그래프 스펙 경로
- `metrics` (object): `string -> int` 맵

### 메트릭 네이밍 (v1)

기본 키(러너 제공):

- `packets.consumed_total`
- `packets.produced_total`
- `packets.source_emitted_total`
- `packets.dropped_total` (inbox overflow, backpressure 정책)
- `node.<node_id>.consumed`
- `node.<node_id>.produced`
- `node.<node_id>.is_source` (0|1)
- `node.<node_id>.is_sink` (0|1)
- `node.<node_id>.inbox_dropped_total` (inbox overflow, 러너 강제)

확장 키(노드 제공, 선택):

- `node.<node_id>.<metric_name>` (int만 허용; 예: `node.queue.queue_depth`)
