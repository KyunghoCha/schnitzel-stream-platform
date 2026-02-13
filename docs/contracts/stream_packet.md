# StreamPacket Contract v1 (PROVISIONAL)

## English

### Purpose

`StreamPacket` is the universal node-to-node data contract for `schnitzel_stream`.

Intent:
- Keep Phase 1 contract **small and stable**.
- Avoid baking in CCTV/video assumptions (OpenCV types, backend schema, etc).
- Allow multiple transports later (in-proc, IPC, network) via explicit adapters.

### Schema (v1)

- `packet_id` (string): unique packet id (UUID recommended)
- `ts` (string): ISO-8601 timestamp (UTC recommended)
- `kind` (string): payload semantics (examples: `frame`, `event`, `sensor`, `metrics`, `control`)
- `source_id` (string): origin stream id (camera_id, sensor_id, topic, etc)
- `payload` (any): actual data
- `meta` (object): small metadata map (must be JSON-serializable if transported)

### Invariants / Rules

- Nodes must communicate **only** via `StreamPacket` once the graph runtime is enabled (Phase 1+).
- `meta` must not include secrets. Treat it as loggable by default.
- Large/binary payloads:
  - Phase 1: in-process objects are allowed (e.g., numpy frame), but this must be treated as **non-portable**.
  - Phase 2+: cross-process/network requires an explicit encoding/handle strategy (e.g., shared-memory handle, file reference, chunking).

### Examples

Event packet (payload is backend protocol dict):

```jsonc
{
  "packet_id": "uuid-...",
  "ts": "2026-02-13T00:00:00Z",
  "kind": "event",
  "source_id": "cam01",
  "payload": {
    "event_id": "uuid-...",
    "event_type": "ZONE_INTRUSION"
  },
  "meta": {
    "schema_version": "event_protocol_v0.2"
  }
}
```

Sensor packet (payload is sensor adapter output):

```jsonc
{
  "packet_id": "uuid-...",
  "ts": "2026-02-13T00:00:00Z",
  "kind": "sensor",
  "source_id": "ultrasonic-front-01",
  "payload": {
    "distance_cm": 82.4
  },
  "meta": {}
}
```

---

## 한국어

### 목적

`StreamPacket`은 `schnitzel_stream`의 노드 간 데이터 교환을 위한 범용 계약입니다.

의도(Intent):
- Phase 1 계약은 **작고 안정적**이어야 합니다.
- CCTV/비디오(OpenCV 타입, 백엔드 이벤트 스키마 등) 가정을 코어 계약에 박지 않습니다.
- 향후 다양한 전송(in-proc, IPC, 네트워크)을 명시적 어댑터로 지원할 수 있어야 합니다.

### 스키마 (v1)

- `packet_id` (string): 패킷 고유 ID (UUID 권장)
- `ts` (string): ISO-8601 타임스탬프 (UTC 권장)
- `kind` (string): 페이로드 의미 (예: `frame`, `event`, `sensor`, `metrics`, `control`)
- `source_id` (string): 원본 스트림 식별자 (camera_id, sensor_id, topic 등)
- `payload` (any): 실제 데이터
- `meta` (object): 작은 메타데이터 맵 (전송 시 JSON 직렬화 가능해야 함)

### 불변조건 / 규칙

- 그래프 런타임이 활성화되면(Phase 1+), 노드는 **오직** `StreamPacket`으로만 통신합니다.
- `meta`에는 비밀정보를 넣지 않습니다. 기본적으로 로그에 찍힐 수 있다고 가정합니다.
- 큰/바이너리 payload:
  - Phase 1: 프로세스 내부 객체(numpy frame 등)를 허용하되, 이는 **이식 불가(non-portable)** 로 취급합니다.
  - Phase 2+: 프로세스/네트워크 경계를 넘으려면 인코딩/핸들 전략을 명시해야 합니다(예: shared-memory handle, 파일 참조, 청크 전송).

### 예시

이벤트 패킷(백엔드 프로토콜 dict를 payload로 사용):

```jsonc
{
  "packet_id": "uuid-...",
  "ts": "2026-02-13T00:00:00Z",
  "kind": "event",
  "source_id": "cam01",
  "payload": {
    "event_id": "uuid-...",
    "event_type": "ZONE_INTRUSION"
  },
  "meta": {
    "schema_version": "event_protocol_v0.2"
  }
}
```

센서 패킷(센서 어댑터 출력이 payload):

```jsonc
{
  "packet_id": "uuid-...",
  "ts": "2026-02-13T00:00:00Z",
  "kind": "sensor",
  "source_id": "ultrasonic-front-01",
  "payload": {
    "distance_cm": 82.4
  },
  "meta": {}
}
```

