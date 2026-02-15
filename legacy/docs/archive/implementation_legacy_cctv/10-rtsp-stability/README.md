# RTSP Stability

## English

## Status

Implemented in `src/ai/pipeline/sources/rtsp.py` (`RtspSource`) and `src/ai/pipeline/core.py`.

## Notes

- If RTSP reads fail, the pipeline stays alive and retries with backoff + jitter.
- When the RTSP source successfully reconnects, the next loop skips extra pipeline sleep once.
- After reconnect, the pipeline still sleeps a minimal delay to avoid tight loops.
- If `rtsp.max_attempts` is set and exceeded, reconnect stops and the pipeline exits.
- Live sources are automatically wrapped with `ThreadedSource` to decouple frame reading from model inference. This prevents FFmpeg buffer overflow and I-frame loss caused by blocking `read()` calls.
- Host E2E uses mock backend on `MOCK_BACKEND_PORT` (default 18080) to avoid port conflicts.
- If the port is already in use, the script auto-selects a free port and writes it to `status.txt`.
- Reconnect cycle test (cross-platform): `python scripts/check_rtsp.py` (시스템에 맞는 MediaMTX 자동 다운로드).
- Legacy bash script: `legacy/scripts/rtsp_e2e_stability.sh` (Linux only).
- Real RTSP environment validation is still pending.

## Code Mapping

- RTSP source: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)
- Threaded wrapper: `src/ai/pipeline/sources/threaded.py` (`ThreadedSource`)
- Retry/backoff in core: `src/ai/pipeline/core.py`

## 한국어

## 상태

`src/ai/pipeline/sources/rtsp.py` (`RtspSource`) 및 `src/ai/pipeline/core.py`에 구현됨.

## 노트

- RTSP read 실패 시 파이프라인이 종료되지 않고 백오프 + 지터로 재시도한다.
- RTSP 소스가 재연결에 성공하면 다음 루프에서 파이프라인 추가 sleep을 1회 생략한다.
- 재연결 직후에도 스핀 방지를 위해 최소 지연을 둔다.
- `rtsp.max_attempts`를 설정했는데 초과하면 재연결을 중단하고 파이프라인이 종료된다.
- 라이브 소스는 자동으로 `ThreadedSource`로 래핑되어 프레임 수신과 모델 추론이 분리된다. 이로써 FFmpeg 내부 버퍼 오버플로우와 I-frame 손실로 인한 디코더 깨짐을 방지한다.
- Host E2E는 `MOCK_BACKEND_PORT`(기본 18080)로 mock backend를 띄워 포트 충돌을 피한다.
- 포트가 이미 사용 중이면 스크립트가 사용 가능한 포트를 자동 선택하고 `status.txt`에 기록한다.
- 재연결 반복 테스트 (크로스 플랫폼): `python scripts/check_rtsp.py` (시스템에 맞는 MediaMTX 자동 다운로드).
- 기존 bash 스크립트: `legacy/scripts/rtsp_e2e_stability.sh` (Linux 전용).
- 실제 RTSP 환경 검증은 아직 진행 전이다.

## 코드 매핑

- RTSP 소스: `src/ai/pipeline/sources/rtsp.py` (`RtspSource`)
- 스레드 래퍼: `src/ai/pipeline/sources/threaded.py` (`ThreadedSource`)
- 코어 재시도/백오프: `src/ai/pipeline/core.py`
