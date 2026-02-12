# Zones & Rules

## English

## Status

Implemented in `src/ai/rules/zones.py` and wired into the pipeline.
Zone loading is controlled by `configs/default.yaml` (`zones.*`, `rules.rule_point_by_event_type`).
Zone source uses TTL cache for both API and file modes.
API failure fallback to cached zones is covered by integration tests.

## Code Mapping

- Zone logic: `src/ai/rules/zones.py`
- Geometry (IoU): `src/ai/vision/geometry.py`
- Wiring: `src/ai/pipeline/__main__.py`

## 한국어

## 상태

`src/ai/rules/zones.py`에 구현되어 파이프라인에 연결됨.
Zone 로딩은 `configs/default.yaml`의 `zones.*`, `rules.rule_point_by_event_type`로 제어된다.
API/파일 모드 모두 TTL 캐시를 사용한다.
API 실패 시 캐시 폴백은 통합 테스트로 검증한다.

## 코드 매핑

- zone 로직: `src/ai/rules/zones.py`
- 기하(IoU): `src/ai/vision/geometry.py`
- 연결: `src/ai/pipeline/__main__.py`
