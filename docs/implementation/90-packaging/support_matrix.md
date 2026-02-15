# Support Matrix (Edge-First)

Last updated: 2026-02-15

## English

### Summary

- **SSOT docs used**: `docs/roadmap/execution_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/contracts/stream_packet.md`.
- **Scope**: Finalize the Phase 9.1 support matrix and packaging lane policy.
- **Policy**: Docker is recommended for Linux production ops, but **not required** for platform correctness.

### Target Matrix

| Tier | OS | Arch | Lane | Status | Notes |
|---|---|---|---|---|---|
| T1 | Linux | amd64 | no-Docker (`pip` + venv) | Supported | CI validated |
| T1 | Linux | amd64 | Docker | Supported | `Dockerfile` path maintained |
| T1 | Linux | arm64 | no-Docker (`pip` + venv) | Supported | Runtime target; device-level validation by deployment |
| T1 | Windows | amd64 | no-Docker (`pip` + venv) | Supported | CI validated |
| T1 | macOS | amd64/arm64 | no-Docker (`pip` + venv) | Supported | CI validated |
| T2 | Linux (Raspberry Pi class) | arm64 | no-Docker (`pip` + venv) | Best effort | Plugin/runtime dependency differences may apply |
| T2 | Linux (Jetson class) | arm64 | custom accelerator lane | Best effort | CUDA/TensorRT stack is deployment-owned |

### Packaging Lanes (Finalized for P9.1)

1. **Lane A (Canonical)**: no-Docker source run (`python -m schnitzel_stream` with venv + `PYTHONPATH=src`).
2. **Lane B (Ops Convenience)**: Docker image run for Linux operations.
3. **Lane C (Deployment-specific)**: accelerator-specific/custom plugin stacks (out of core SSOT).

### CI Contract

- Mandatory CI matrix: `ubuntu-latest`, `windows-latest`, `macos-latest` on Python 3.11.
- Mandatory no-Docker smoke lane on Ubuntu:
  - install deps via `pip`
  - `python3 -m compileall -q src tests`
  - validate representative v2 graphs
  - run one dependency-light v2 graph end-to-end

### Practical Guidance

- Build portable graphs around JSON payload lanes for cross-boundary transport.
- Keep OpenCV/model/GPU dependencies behind plugin boundaries.
- Treat platform core compatibility separately from deployment plugin compatibility.

### Verification

- This document is enforced by `.github/workflows/ci.yml` (test matrix + no-Docker smoke lane).

### Open Questions (deferred to P9.2)

- Service-mode conventions by OS (systemd/Windows Service/launchd).
- Standard logging/storage path defaults for long-running edge ops.

---

## 한국어

### 요약

- **참조 SSOT 문서**: `docs/roadmap/execution_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/contracts/stream_packet.md`.
- **범위**: Phase 9.1 지원 매트릭스와 패키징 레인 정책 확정.
- **정책**: Linux 운영에서 Docker를 권장하지만, 플랫폼 정합성의 필수 조건은 아님.

### 타겟 매트릭스

| Tier | OS | Arch | 레인 | 상태 | 비고 |
|---|---|---|---|---|---|
| T1 | Linux | amd64 | no-Docker (`pip` + venv) | Supported | CI 검증 |
| T1 | Linux | amd64 | Docker | Supported | `Dockerfile` 경로 유지 |
| T1 | Linux | arm64 | no-Docker (`pip` + venv) | Supported | 런타임 타겟, 장비 실검증은 배포 책임 |
| T1 | Windows | amd64 | no-Docker (`pip` + venv) | Supported | CI 검증 |
| T1 | macOS | amd64/arm64 | no-Docker (`pip` + venv) | Supported | CI 검증 |
| T2 | Linux (Raspberry Pi 계열) | arm64 | no-Docker (`pip` + venv) | Best effort | 플러그인/런타임 의존성 차이 가능 |
| T2 | Linux (Jetson 계열) | arm64 | 가속기 전용 커스텀 레인 | Best effort | CUDA/TensorRT 스택은 배포 책임 |

### 패키징 레인 (P9.1 확정)

1. **Lane A (정본)**: no-Docker 소스 실행 (venv + `PYTHONPATH=src` + `python -m schnitzel_stream`).
2. **Lane B (운영 편의)**: Linux 운영용 Docker 이미지 실행.
3. **Lane C (배포 전용)**: 가속기/커스텀 플러그인 스택 (코어 SSOT 범위 밖).

### CI 계약

- 필수 CI 매트릭스: Python 3.11 + `ubuntu-latest`/`windows-latest`/`macos-latest`.
- 필수 Ubuntu no-Docker 스모크 레인:
  - `pip`로 의존성 설치
  - `python3 -m compileall -q src tests`
  - 대표 v2 그래프 validate
  - 의존성 가벼운 v2 그래프 1개 E2E 실행

### 실무 가이드

- 경계 간 전송이 필요한 그래프는 JSON payload 레인 중심으로 설계.
- OpenCV/모델/GPU 의존성은 플러그인 경계 뒤로 격리.
- 플랫폼 코어 호환성과 배포 플러그인 호환성을 분리해 판단.

### 검증

- 이 문서는 `.github/workflows/ci.yml`(테스트 매트릭스 + no-Docker 스모크 레인)로 강제됩니다.

### 미해결 질문 (P9.2로 이관)

- OS별 서비스 모드 규약(systemd/Windows Service/launchd).
- 장기 실행 엣지 운영의 표준 로그/저장 경로 기본값.
