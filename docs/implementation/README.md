# Implementation Docs Index

## English
Overview
--------
This folder organizes implementation notes as a directory tree. Each topic has
its own folder with a README/spec as needed.

Tree
----
00-overview/            High-level plan and scope (+ policy decisions)
10-rtsp-stability/      RTSP reconnect/timeout/health
20-zones-rules/         Zone loading + rule evaluation
25-model-tracking/      Tracker integration (IOU/ByteTrack done, DeepSORT pending)
30-event-dedup/         Cooldown + dedup logic
40-snapshot/            Snapshot save + path policy
50-backend-integration/ Event schema + API details
60-observability/       Metrics + logging + health
70-config/              Config schema + env overrides
80-testing/             Unit/integration/regression tests
90-packaging/           Docker/run/ops

## 한국어
개요
----
이 폴더는 구현 노트를 디렉터리 트리로 정리한다. 각 주제는 필요에 따라
README/spec을 포함한다.

트리
----
00-overview/            상위 계획 및 범위(+ 정책 결정)
10-rtsp-stability/      RTSP 재연결/타임아웃/상태
20-zones-rules/         Zone 로딩 + 룰 평가
25-model-tracking/      트래커 연동(IOU/ByteTrack 완료, DeepSORT 보류)
30-event-dedup/         쿨다운 + 중복 억제 로직
40-snapshot/            스냅샷 저장 + 경로 정책
50-backend-integration/ 이벤트 스키마 + API 세부
60-observability/       메트릭 + 로깅 + 헬스
70-config/              설정 스키마 + env 오버라이드
80-testing/             unit/integration/regression 테스트
90-packaging/           Docker/run/ops
