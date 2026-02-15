# Packaging

Last updated: 2026-02-15

## English

Status
------

- Phase 9.1 baseline is finalized.
- Packaging policy uses two official lanes:
  - no-Docker lane (canonical)
  - Docker lane (Linux ops convenience)

Code Mapping
------------

- Entrypoint: `src/schnitzel_stream/cli/__main__.py`
- Default command: `python -m schnitzel_stream`
- Docker image: `Dockerfile`
- Support matrix SSOT: `docs/implementation/90-packaging/support_matrix.md`
- Edge ops conventions: `docs/implementation/90-packaging/ops/spec.md`, `docs/implementation/90-packaging/ops/design.md`
- CI enforcement: `.github/workflows/ci.yml`

Lane A: no-Docker (Canonical)
-----------------------------

```bash
python3 -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
export PYTHONPATH=src
python -m schnitzel_stream validate --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 10
```

Lane B: Docker (Linux Ops)
--------------------------

```bash
docker build -t schnitzel-stream-platform .
docker run --rm schnitzel-stream-platform python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 10
```

Notes
-----

- Cross-platform correctness is guaranteed by the no-Docker lane.
- Deployment-specific accelerators (CUDA/TensorRT/DirectML) remain plugin-owned.

## 한국어

상태
----

- Phase 9.1 기준선 확정 완료.
- 공식 패키징 레인은 2개:
  - no-Docker 레인(정본)
  - Docker 레인(Linux 운영 편의)

코드 매핑
---------

- 엔트리포인트: `src/schnitzel_stream/cli/__main__.py`
- 기본 실행: `python -m schnitzel_stream`
- Docker 이미지: `Dockerfile`
- 지원 매트릭스 SSOT: `docs/implementation/90-packaging/support_matrix.md`
- 엣지 운영 규약: `docs/implementation/90-packaging/ops/spec.md`, `docs/implementation/90-packaging/ops/design.md`
- CI 강제 지점: `.github/workflows/ci.yml`

Lane A: no-Docker (정본)
------------------------

```bash
python3 -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
export PYTHONPATH=src
python -m schnitzel_stream validate --graph configs/graphs/dev_inproc_demo_v2.yaml
python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 10
```

Lane B: Docker (Linux 운영)
---------------------------

```bash
docker build -t schnitzel-stream-platform .
docker run --rm schnitzel-stream-platform python -m schnitzel_stream --graph configs/graphs/dev_inproc_demo_v2.yaml --max-events 10
```

노트
----

- 크로스플랫폼 정합성의 기준은 no-Docker 레인입니다.
- 가속기별 의존성(CUDA/TensorRT/DirectML)은 배포 플러그인 책임으로 유지합니다.
