# Backpressure Fairness Paper Plan

Last updated: 2026-02-23

## English

## Motivation

This paper targets a practical ethical question in stream processing systems:

- Under backpressure, two policies with similar average throughput can produce very different harm distributions across groups.
- Existing runtime benchmarks usually optimize latency/throughput only and under-report fairness-sensitive failure patterns.
- We need a reproducible method to evaluate policy choice as an ethical systems decision.

## Scope

- In scope:
  - Backpressure policy comparison on synthetic but reproducible workloads.
  - Group-sensitive metrics (`group_miss_gap`, `group_latency_gap_ms`, `harm_weighted_cost`).
  - Native runtime vs ROS2 baseline comparison on identical metric schema.
- Out of scope:
  - Distributed orchestrator implementation.
  - Personal/identifiable data ingestion.
  - Full ROS2 production architecture benchmarking.

## Experiment Matrix

- Policies: `drop_new`, `drop_oldest`, `error`, `weighted_drop`
- Workloads: `balanced`, `skewed_burst`, `recovery_stress`, `minority_spike`
- Repeats: `50` per policy-workload pair (paper-grade default)

## Reproducible Commands

Run benchmark sessions:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/run_backpressure_bench.py \
  --base configs/experiments/backpressure_fairness/bench_base.yaml
```

Aggregate and compute pairwise significance/effect sizes:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/aggregate_backpressure_results.py \
  --runs-glob 'outputs/experiments/backpressure_fairness/session_*/runs/run_*.json' \
  --out-dir outputs/experiments/backpressure_fairness/aggregate
```

Build tables/plots:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/plot_backpressure_results.py \
  --aggregate-json outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json

conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/build_research_tables.py \
  --aggregate-json outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json
```

Compare with ROS2 baseline runs:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/compare_ros2_baseline.py \
  --native-runs-glob 'outputs/experiments/backpressure_fairness/session_*/runs/run_*.json' \
  --ros2-runs-glob 'outputs/experiments/backpressure_fairness/ros2_baseline/session_*/runs/run_*.json'
```

## Outputs

- Aggregate: `backpressure_aggregate.json`, `backpressure_summary.csv`, `backpressure_pairwise_tests.csv`
- Tables: `research_tables.md`, `table_pairwise_significance.csv`
- ROS2 compare: `ros2_comparison.json`, `ros2_comparison.csv`, `ros2_reproducibility.csv`

## 한국어

## 동기

이 논문은 스트림 시스템에서의 실용적 윤리 문제를 다룬다.

- 백프레셔 상황에서 평균 처리량이 비슷한 정책도 집단별 손해 분포는 크게 달라질 수 있다.
- 기존 런타임 벤치는 지연/처리량 중심이라 공정성 민감 실패 패턴을 충분히 드러내지 못한다.
- 정책 선택을 윤리적 시스템 의사결정으로 평가할 수 있는 재현 가능한 방법이 필요하다.

## 범위

- 포함:
  - 재현 가능한 합성 워크로드 기반 백프레셔 정책 비교
  - 집단 민감 지표(`group_miss_gap`, `group_latency_gap_ms`, `harm_weighted_cost`)
  - 동일 지표 스키마 기준 Native 런타임 vs ROS2 비교
- 제외:
  - 분산 오케스트레이터 구현
  - 개인정보/식별 가능 데이터 사용
  - ROS2 전체 프로덕션 아키텍처 성능평가

## 실험 매트릭스

- 정책: `drop_new`, `drop_oldest`, `error`, `weighted_drop`
- 워크로드: `balanced`, `skewed_burst`, `recovery_stress`, `minority_spike`
- 반복: 정책-워크로드 조합당 `50`회(논문 기본값)

## 재현 명령어

벤치 실행:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/run_backpressure_bench.py \
  --base configs/experiments/backpressure_fairness/bench_base.yaml
```

집계 + 유의성/효과크기 계산:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/aggregate_backpressure_results.py \
  --runs-glob 'outputs/experiments/backpressure_fairness/session_*/runs/run_*.json' \
  --out-dir outputs/experiments/backpressure_fairness/aggregate
```

표/플롯 생성:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/plot_backpressure_results.py \
  --aggregate-json outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json

conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/build_research_tables.py \
  --aggregate-json outputs/experiments/backpressure_fairness/aggregate/backpressure_aggregate.json
```

ROS2 비교:

```bash
conda run -n schnitzel-stream env PYTHONPATH=src python scripts/experiments/compare_ros2_baseline.py \
  --native-runs-glob 'outputs/experiments/backpressure_fairness/session_*/runs/run_*.json' \
  --ros2-runs-glob 'outputs/experiments/backpressure_fairness/ros2_baseline/session_*/runs/run_*.json'
```

## 산출물

- 집계: `backpressure_aggregate.json`, `backpressure_summary.csv`, `backpressure_pairwise_tests.csv`
- 표: `research_tables.md`, `table_pairwise_significance.csv`
- ROS2 비교: `ros2_comparison.json`, `ros2_comparison.csv`, `ros2_reproducibility.csv`
