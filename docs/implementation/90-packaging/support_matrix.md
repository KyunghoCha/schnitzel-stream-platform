# Support Matrix (Edge-First, PROVISIONAL)

Last updated: 2026-02-13

## English

### Summary

- **SSOT docs used**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **Scope**: Define a pragmatic support matrix and packaging strategy for "runs on almost all edges" goals.
- **Non-scope**: GPU/accelerator-specific builds (Jetson/CUDA/DirectML) are not standardized in Phase 0.

### Risks (P0–P3)

- **P0**: A single packaging method will not cover all edge environments (Docker unavailable, restricted OS images, no compiler toolchain).
- **P1**: OpenCV and video decode dependencies vary by OS/arch; binary wheels may not exist for niche targets.
- **P2**: Windows service/daemonization semantics differ from Linux systemd; operational parity requires extra work.
- **P3**: Shipping "one binary" builds can mask dynamic dependency issues and complicate debugging.

### Mismatches (path)

- None found. (This document establishes the current support intent; implementation will be incremental.)

### Fix Plan

1. **Baseline runtime** (Phase 0):
   - Python **3.11** (CI baseline).
   - Entrypoint: `python -m schnitzel_stream`.
2. **Primary distribution (Linux edges)**:
   - Use Docker images (multi-arch): `linux/amd64`, `linux/arm64`.
   - Build via `docker buildx` in CI when ready.
3. **Developer distribution (Windows/macOS/Linux)**:
   - Run from source with `PYTHONPATH=src` and a venv.
   - Keep dependencies minimal; keep heavy runtimes as optional requirements files.
4. **Optional "single artifact" distribution (select targets)**:
   - Evaluate PyInstaller/Nuitka only after Phase 1 runtime boundaries are clearer.
   - Treat as convenience builds, not the primary ops path.
5. **Operational contracts**:
   - Repo-root relative configs: `configs/*`.
   - Writable paths must be explicit (snapshots/logs/outputs) and documented per target.

### Verification

- Executed: N/A (doc-only change).
- Not executed: N/A.

### Open Questions

- What is the official target list?
  - OS: Linux, Windows, macOS
  - Arch: amd64, arm64
  - Edge class: Raspberry Pi / industrial PC / Jetson
- Do we require Docker on all production edges, or do we need a "no-Docker" packaging lane?
- How should we handle GPU acceleration portability (CUDA vs OpenVINO vs DirectML)?

---

## 한국어

### 요약

- **참조 SSOT 문서**: `docs/roadmap/strategic_roadmap.md`, `docs/design/architecture_2.0.md`, `docs/implementation/90-packaging/entrypoint/design.md`, `PROMPT_CORE.md`.
- **범위**: “거의 모든 엣지에서 실행” 목표를 위한 현실적인 지원 매트릭스와 패키징 전략을 정의합니다.
- **비범위**: GPU/가속기별 빌드(Jetson/CUDA/DirectML)는 Phase 0에서 표준화하지 않습니다.

### 리스크 (P0–P3)

- **P0**: 단일 패키징 방식으로 모든 엣지 환경을 커버할 수 없습니다(Docker 불가, 제한된 OS 이미지, 컴파일러 툴체인 부재 등).
- **P1**: OpenCV/비디오 디코드 의존성은 OS/arch에 따라 달라지며, 일부 타겟은 바이너리 휠이 없을 수 있습니다.
- **P2**: Windows 서비스/데몬 의미론은 Linux(systemd)와 달라 운영 동등성을 위해 추가 작업이 필요합니다.
- **P3**: “단일 바이너리” 배포는 동적 의존성 문제를 가릴 수 있고, 디버깅을 어렵게 만들 수 있습니다.

### 불일치(경로)

- 발견된 불일치 없음. (이 문서는 지원 의도(intent)를 정의하며, 구현은 점진적으로 진행합니다.)

### 실행 계획

1. **기본 런타임** (Phase 0):
   - Python **3.11** (CI 기준).
   - 엔트리포인트: `python -m schnitzel_stream`.
2. **주 배포 경로(리눅스 엣지)**:
   - Docker 이미지(multi-arch): `linux/amd64`, `linux/arm64`.
   - 준비되면 CI에서 `docker buildx`로 빌드.
3. **개발자 배포(Windows/macOS/Linux)**:
   - 소스 실행 + venv + `PYTHONPATH=src`.
   - 의존성은 최소화하고, 무거운 런타임은 옵션 requirements로 분리.
4. **선택적 단일 아티팩트 배포(일부 타겟)**:
   - Phase 1 런타임 경계가 더 명확해진 뒤 PyInstaller/Nuitka를 평가.
   - 운영 기본 경로가 아닌 convenience build로 취급.
5. **운영 계약(contracts)**:
   - repo-root 상대 config: `configs/*`.
   - writable 경로(스냅샷/로그/출력)는 타겟별로 명시하고 문서화.

### 검증

- 실행됨: 해당 없음(문서 변경).
- 실행 안 함: 해당 없음.

### 미해결 질문

- 공식 타겟 리스트는?
  - OS: Linux, Windows, macOS
  - Arch: amd64, arm64
  - Edge class: Raspberry Pi / industrial PC / Jetson
- 프로덕션 엣지에서 Docker를 필수로 할 것인가, 아니면 “no-Docker” 패키징 레인이 필요한가?
- GPU 가속 이식성(CUDA vs OpenVINO vs DirectML)을 어떻게 다룰 것인가?
