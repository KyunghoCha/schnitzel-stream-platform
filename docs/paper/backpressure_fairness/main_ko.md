# Backpressure Fairness in Stream Processing (한글 원고)

## English
This document is the Korean full-text version of the backpressure fairness manuscript.
Primary manuscript source remains `docs/paper/backpressure_fairness/main.tex`.

## 한국어
## 초록
본 연구는 백프레셔 상황에서 큐 오버플로우 정책이 공정성 관련 성능에 미치는 영향을 고정된 분석 규약으로 평가한다.  
Native와 ROS2 baseline 모두 동일한 스키마로 `4 정책 x 4 워크로드 x 50 반복 = 800 run`을 수행했다.  
Native 결과에서 workload별 1위 정책은 단일하지 않았다. `balanced/recovery_stress`는 `weighted_drop`, `minority_spike`는 `drop_oldest`, `skewed_burst`는 `drop_new`가 1위였다.  
Pairwise 72개 비교 중 Holm 보정 후 유의한 결과는 10개였고, 모두 `harm_weighted_cost` 또는 `p95_latency_ms`에서만 나타났다.  
`error` 정책의 실패 결과는 제외하지 않고 그대로 보고했다.  
ROS2 비교는 부록 보조 근거로만 사용한다.

## 1. 서론
큐 오버플로우 정책은 보통 운영 파라미터로 취급되지만, 공정성 민감 파이프라인에서는 정책 선택이 그룹별 피해 분포를 바꿀 수 있다.  
본 문서는 실험 후 기준 변경을 금지한 analysis freeze 기반으로, 정책 간 차이를 관측치 중심으로 보고한다.  
핵심 주장은 native 결과에 한정하며, ROS2는 동일 스키마 비교를 위한 부록 증거로 분리한다.

## 2. 연구 범위와 전제
- 단일 진실 소스: `outputs/experiments/backpressure_fairness/paper_submission_final_ros2`
- 사후 수기 입력 금지: 모든 수치는 JSON/CSV 산출물에서만 인용
- 인과 단정 금지: 관측 비교까지만 서술
- 비유의 결과/불리한 결과 포함 의무

## 3. 방법
### 3.1 실험 매트릭스
- 정책: `drop_new`, `drop_oldest`, `error`, `weighted_drop`
- 워크로드: `balanced`, `skewed_burst`, `recovery_stress`, `minority_spike`
- 반복: 각 조합 50회, seed 규칙 고정

### 3.2 통계 규약
- bootstrap 95% CI
- Mann-Whitney U (two-sided)
- Holm-Bonferroni 보정 (`alpha=0.05`)
- Cliff's delta (효과크기)

### 3.3 실행 환경 분리
- Native 단계: conda `schnitzel-stream`
- ROS2 단계: `/usr/bin/python3` + `source /opt/ros/humble/setup.bash`

## 4. 결과
### 4.1 핵심 메트릭
`error` 정책은 모든 워크로드에서 `ok_count=0`, 즉 50/50 실패였다(총 200 실패).  
비오류 정책에서 `drop_rate`와 `event_miss_rate`는 workload 내 정책 간 동일했다.

### 4.2 공정성 메트릭
비오류 정책의 `group_miss_gap_mean`은 전 조합에서 0.0이었다.  
`group_latency_gap_ms_mean`은 수치 차이가 있었지만 Holm 보정 후 유의하지 않았다.

### 4.3 workload별 정책 순위
- `balanced`: `weighted_drop` 1위
- `minority_spike`: `drop_oldest` 1위
- `recovery_stress`: `weighted_drop` 1위
- `skewed_burst`: `drop_new` 1위

### 4.4 유의성 결과
- 총 72개 pairwise 중 유의 10개
- 유의 메트릭: `harm_weighted_cost`(5), `p95_latency_ms`(5)
- 비유의 메트릭: `drop_rate`, `event_miss_rate`, `group_miss_gap`, `group_latency_gap_ms`

### 4.5 그래프 해석
영문 원고 `results.tex`에는 CI 포함 점-에러바 그래프를 배치했다.
- 피해비용 그래프: `figures/*__harm_weighted_cost_mean.png`
- 지연시간 그래프: `figures/*__p95_latency_ms_mean.png`

`error` 정책은 0으로 그리지 않고 `NA`(실패/결측)로 표시했다.

## 5. 논의
관측상 정책 순위는 workload 의존적이며, 단일 정책의 전역 우월성은 확인되지 않는다.  
Recovery-stress에서는 평균 차이가 작고 Holm 유의에 도달하지 않았다.  
본 연구는 합성 workload와 설정된 harm 가중치에 의존하므로 외적 타당성은 제한된다.

## 6. 결론
고정된 분석 규약에서 정책 효과는 workload마다 다르게 나타났다.  
유의한 차이는 일부 메트릭(`harm_weighted_cost`, `p95_latency_ms`)에 집중됐고, 나머지 메트릭은 유의하지 않았다.  
제출 가능한 재현 패키지를 갖췄지만, 해석은 본 실험 설정 범위로 제한한다.

## 부록 A. ROS2 비교 요약
ROS2 baseline은 본문 핵심 주장 검증이 아니라 부록 보조 비교다.  
이번 설정에서는 비교 가능한 셀에서 native가 harm/p95 평균에서 일관되게 낮았다.  
재현성 지표(CV)는 ROS2가 더 큰 분산을 보였다.

## 재현 경로
- 메인 영문 LaTeX: `docs/paper/backpressure_fairness/main.tex`
- 영문 결과 섹션: `docs/paper/backpressure_fairness/sections/results.tex`
- 산출물 manifest: `outputs/experiments/backpressure_fairness/paper_submission_final_ros2/package/artifacts_manifest.json`
