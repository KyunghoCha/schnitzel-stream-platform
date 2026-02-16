# Professor Showcase Guide

Last updated: 2026-02-16

## English

This guide defines the reproducible professor demo flow for the P11 showcase package.

## Scope

- S1: in-proc baseline (`showcase_inproc_v2.yaml`)
- S2: durable enqueue + drain/ack (`showcase_durable_*`)
- S3: webcam pipeline (`showcase_webcam_v2.yaml`)

The one-command profile runner is `scripts/demo_pack.py`.

## Prerequisites Checklist

1. Python 3.11 environment with dependencies installed:
   - `pip install -r requirements.txt -r requirements-dev.txt`
2. Environment doctor reports required checks as pass:
   - `python scripts/env_doctor.py --strict`
3. Runtime entrypoint works:
   - `python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml`
4. For S3:
   - Webcam device is available.
   - OpenCV import works in the environment.

## One-Command Demo

CI-safe profile (no webcam):

```bash
python scripts/demo_pack.py --profile ci
```

Professor profile (includes webcam):

```bash
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

Default report:
- `outputs/reports/demo_pack_latest.json`
- report schema: `schema_version=2`
- failure fields (when failed): `failure_kind`, `failure_reason`

Static summary rendering:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

Exit codes:
- `0`: success
- `1`: runtime failure (non-webcam)
- `2`: validation failure
- `20`: webcam run failure in professor profile

## Manual Fallback Runbook

### S1: in-proc baseline

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_inproc_v2.yaml --max-events 50
```

Expected output:
- lines prefixed with `SHOWCASE`

### S2: durable enqueue + drain/ack

Reset queue file:

```bash
# Linux/macOS
rm -f outputs/queues/showcase_demo.sqlite3
```

```powershell
# Windows PowerShell
Remove-Item outputs/queues/showcase_demo.sqlite3 -ErrorAction SilentlyContinue
```

Run:

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_enqueue_v2.yaml
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_durable_enqueue_v2.yaml --max-events 50
python -m schnitzel_stream --graph configs/graphs/showcase_durable_drain_ack_v2.yaml --max-events 50
```

Expected output:
- drain lines prefixed with `SHOWCASE_DRAIN`

### S3: webcam pipeline

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_webcam_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_webcam_v2.yaml --max-events 50
```

Expected output:
- lines prefixed with `WEBCAM`

## Troubleshooting

1. `No module named omegaconf` or plugin import errors:
   - Run `python scripts/env_doctor.py --strict` first.
   - Install baseline dependencies again: `pip install -r requirements.txt`
   - Confirm report field: `failure_kind=environment`, `failure_reason=dependency_missing`
2. Webcam profile exits with code `20`:
   - Check device index (`--camera-index`), close camera-using apps, rerun.
   - Confirm report field: `failure_reason=webcam_runtime_failed`
3. Durable replay seems inconsistent:
   - Remove `outputs/queues/showcase_demo.sqlite3` and rerun S2.
4. Command not found for `pytest`/`pip`:
   - Verify active Python environment and PATH.

## 한국어

이 가이드는 P11 쇼케이스 패키지 기준의 교수님 시연 재현 절차를 정의합니다.

## 범위

- S1: in-proc 기본선 (`showcase_inproc_v2.yaml`)
- S2: durable enqueue + drain/ack (`showcase_durable_*`)
- S3: 웹캠 파이프라인 (`showcase_webcam_v2.yaml`)

원커맨드 실행기는 `scripts/demo_pack.py`입니다.

## 사전 준비 체크리스트

1. Python 3.11 환경에서 의존성 설치:
   - `pip install -r requirements.txt -r requirements-dev.txt`
2. 환경 진단에서 필수 항목 통과 확인:
   - `python scripts/env_doctor.py --strict`
3. 런타임 엔트리포인트 검증:
   - `python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml`
4. S3 실행 전:
   - 웹캠 장치 사용 가능
   - OpenCV import 가능

## 원커맨드 데모

CI 안전 프로필(웹캠 제외):

```bash
python scripts/demo_pack.py --profile ci
```

교수님 시연 프로필(웹캠 포함):

```bash
python scripts/demo_pack.py --profile professor --camera-index 0 --max-events 50
```

기본 리포트 경로:
- `outputs/reports/demo_pack_latest.json`
- 리포트 스키마: `schema_version=2`
- 실패 시 분류 필드: `failure_kind`, `failure_reason`

정적 요약 렌더링:

```bash
python scripts/demo_report_view.py --report outputs/reports/demo_pack_latest.json --format both
```

종료 코드:
- `0`: 성공
- `1`: 일반 런타임 실패(웹캠 외)
- `2`: 검증 실패
- `20`: professor 프로필의 웹캠 실행 실패

## 수동 fallback 실행 절차

### S1: in-proc 기본선

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_inproc_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_inproc_v2.yaml --max-events 50
```

기대 출력:
- `SHOWCASE` 접두 라인 출력

### S2: durable enqueue + drain/ack

큐 파일 초기화:

```bash
# Linux/macOS
rm -f outputs/queues/showcase_demo.sqlite3
```

```powershell
# Windows PowerShell
Remove-Item outputs/queues/showcase_demo.sqlite3 -ErrorAction SilentlyContinue
```

실행:

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_enqueue_v2.yaml
python -m schnitzel_stream validate --graph configs/graphs/showcase_durable_drain_ack_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_durable_enqueue_v2.yaml --max-events 50
python -m schnitzel_stream --graph configs/graphs/showcase_durable_drain_ack_v2.yaml --max-events 50
```

기대 출력:
- `SHOWCASE_DRAIN` 접두 라인 출력

### S3: 웹캠 파이프라인

```bash
python -m schnitzel_stream validate --graph configs/graphs/showcase_webcam_v2.yaml
python -m schnitzel_stream --graph configs/graphs/showcase_webcam_v2.yaml --max-events 50
```

기대 출력:
- `WEBCAM` 접두 라인 출력

## 트러블슈팅

1. `No module named omegaconf` 또는 플러그인 import 오류:
   - 먼저 `python scripts/env_doctor.py --strict` 실행
   - `pip install -r requirements.txt` 재실행
   - 리포트에서 `failure_kind=environment`, `failure_reason=dependency_missing` 확인
2. professor 프로필이 코드 `20`으로 종료:
   - `--camera-index` 확인, 카메라 점유 앱 종료 후 재실행
   - 리포트에서 `failure_reason=webcam_runtime_failed` 확인
3. durable 재생 결과가 일관되지 않음:
   - `outputs/queues/showcase_demo.sqlite3` 삭제 후 S2 재실행
4. `pytest`/`pip` 명령 없음:
   - 활성 파이썬 환경과 PATH 확인
