# Graph Wizard Guide

Last updated: 2026-02-17

## English

`graph_wizard` is a non-interactive CLI helper that generates runnable v2 graph YAML from template profiles.

Command surface:

```bash
python scripts/graph_wizard.py --list-profiles [--experimental]
python scripts/graph_wizard.py --profile <id> --out <path> [options]
python scripts/graph_wizard.py --validate --spec <path>
```

3-step quick path:

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python -m schnitzel_stream --graph configs/graphs/generated_inproc_demo_v2.yaml --max-events 30
```

PowerShell quick path:

```powershell
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile file_frames --out configs/graphs/generated_file_frames_v2.yaml --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30 --validate-after-generate
python -m schnitzel_stream --graph configs/graphs/generated_file_frames_v2.yaml --max-events 30
```

Options:
- `--experimental`: include/generate opt-in profiles
- `--input-path <path>`: override file source path for file-based profiles
- `--camera-index <int>`: override webcam index for webcam-based profiles
- `--device <cpu|0|...>`: override YOLO device
- `--model-path <path>`: override YOLO model path
- `--loop <true|false>`: override file loop behavior
- `--max-events <int>`: propagate a bounded source frame count where template supports `MAX_FRAMES`
- `--validate-after-generate`: run graph validator immediately after generation
- `--json`: machine-readable output mode

Exit codes:
- `0`: success
- `1`: runtime failure
- `2`: usage/input error
- `3`: precondition failure (for example: experimental profile guard or validation failure)

Experimental profile notes:
- `file_yolo_view` and `webcam_yolo` require OpenCV GUI capability.
- YOLO profiles require model dependencies (`requirements-model.txt`) and model file availability.

Generated graph metadata:
- Every generated YAML includes provenance header comments:
  - wizard version
  - profile id
  - generation timestamp (UTC)
  - override summary

## 한국어

`graph_wizard`는 템플릿 프로필에서 실행 가능한 v2 그래프 YAML을 생성하는 비상호작용 CLI 도구다.

명령 표면:

```bash
python scripts/graph_wizard.py --list-profiles [--experimental]
python scripts/graph_wizard.py --profile <id> --out <path> [options]
python scripts/graph_wizard.py --validate --spec <path>
```

3단계 빠른 실행:

```bash
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile inproc_demo --out configs/graphs/generated_inproc_demo_v2.yaml --validate-after-generate
python -m schnitzel_stream --graph configs/graphs/generated_inproc_demo_v2.yaml --max-events 30
```

PowerShell 빠른 실행:

```powershell
python scripts/graph_wizard.py --list-profiles
python scripts/graph_wizard.py --profile file_frames --out configs/graphs/generated_file_frames_v2.yaml --input-path data/samples/2048246-hd_1920_1080_24fps.mp4 --max-events 30 --validate-after-generate
python -m schnitzel_stream --graph configs/graphs/generated_file_frames_v2.yaml --max-events 30
```

옵션:
- `--experimental`: 실험 프로필 목록/생성을 허용
- `--input-path <path>`: file 기반 프로필 입력 경로 override
- `--camera-index <int>`: webcam 기반 프로필 카메라 인덱스 override
- `--device <cpu|0|...>`: YOLO 디바이스 override
- `--model-path <path>`: YOLO 모델 경로 override
- `--loop <true|false>`: file 입력 반복 설정 override
- `--max-events <int>`: 템플릿이 `MAX_FRAMES`를 지원하면 bounded 프레임 수로 반영
- `--validate-after-generate`: 생성 직후 그래프 검증 실행
- `--json`: 자동화용 JSON 출력

종료 코드:
- `0`: 성공
- `1`: 런타임 실패
- `2`: 사용법/입력 오류
- `3`: 사전조건 실패(예: experimental 가드, 검증 실패)

실험 프로필 주의:
- `file_yolo_view`, `webcam_yolo`는 OpenCV GUI 환경이 필요하다.
- YOLO 프로필은 모델 의존성(`requirements-model.txt`)과 모델 파일이 준비되어야 한다.

생성물 메타데이터:
- 생성된 YAML 상단에 provenance 주석이 자동 포함된다.
  - wizard 버전
  - profile id
  - UTC 생성 시각
  - override 요약
