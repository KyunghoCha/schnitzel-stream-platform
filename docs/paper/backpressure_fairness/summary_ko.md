# Backpressure Fairness 논문 한글 요약

## 1) 연구 범위
- 이 문서는 `outputs/experiments/backpressure_fairness/paper_submission_final_ros2` 산출물만 근거로 작성했다.
- 실험 매트릭스: `4 정책 x 4 워크로드 x 50 반복 = 시스템당 800 run`.
- 핵심 주장은 native 결과이며, ROS2 비교는 부록 보조 근거다.

## 2) 핵심 결과
- 워크로드별 1위 정책이 다르다.
  - `balanced`: `weighted_drop`
  - `minority_spike`: `drop_oldest`
  - `recovery_stress`: `weighted_drop`
  - `skewed_burst`: `drop_new`
- pairwise 72개 중 Holm 보정 후 유의한 결과는 10개다.
- 유의한 결과는 `harm_weighted_cost`와 `p95_latency_ms`에서만 나왔다.
- `error` 정책은 모든 워크로드에서 `ok_count=0`으로 실패 결과를 숨기지 않고 그대로 보고했다.

## 3) 그래프 위치
- 논문 삽입용 그래프(PDF):
  - `docs/paper/backpressure_fairness/figures/balanced__harm_weighted_cost_mean.pdf`
  - `docs/paper/backpressure_fairness/figures/minority_spike__harm_weighted_cost_mean.pdf`
  - `docs/paper/backpressure_fairness/figures/recovery_stress__harm_weighted_cost_mean.pdf`
  - `docs/paper/backpressure_fairness/figures/skewed_burst__harm_weighted_cost_mean.pdf`
- 원본 그래프(SVG):
  - `outputs/experiments/backpressure_fairness/paper_submission_final_ros2/plots/*.svg`

## 4) 논문 소스 경로
- 메인: `docs/paper/backpressure_fairness/main.tex`
- 결과 섹션: `docs/paper/backpressure_fairness/sections/results.tex`
- 표: `docs/paper/backpressure_fairness/tables/*.tex`

## 5) 컴파일
```bash
cd ~/Projects/schnitzel-stream-platform/docs/paper/backpressure_fairness
conda run -n schnitzel-stream tectonic --keep-logs --keep-intermediates main.tex
```

