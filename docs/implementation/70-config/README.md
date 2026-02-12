# Config

## English

Status
------

Implemented in `src/ai/config.py` and `src/ai/pipeline/config.py`.
Default config keeps snapshots disabled; enable by setting `events.snapshot.base_dir`.

Config Precedence
-----------------

Configuration is loaded in the following order (later sources override earlier):

1. `configs/default.yaml` (base defaults)
2. `configs/cameras.yaml` (camera-specific settings)
3. `configs/{dev|prod}.yaml` (profile-specific overrides, based on `app.env`)
4. **Environment variables** (highest priority, always override yaml configs)

Code Mapping
------------

- Config loader/merge: `src/ai/config.py`
- Pipeline settings: `src/ai/pipeline/config.py`

## 한국어

상태
----

`src/ai/config.py` 및 `src/ai/pipeline/config.py`에 구현됨.
기본 설정에서는 스냅샷이 비활성화되어 있으며, `events.snapshot.base_dir`를 지정해야 활성화된다.

설정 우선순위
-------------

설정은 다음 순서로 로드됨 (뒤에 오는 것이 앞을 덮어씀):

1. `configs/default.yaml` (기본값)
2. `configs/cameras.yaml` (카메라별 설정)
3. `configs/{dev|prod}.yaml` (프로필별 오버라이드, `app.env` 기준)
4. **환경 변수** (최우선 적용 - 모든 yaml 설정보다 우선함)

코드 매핑
---------

- 설정 로더/병합: `src/ai/config.py`
- 파이프라인 설정: `src/ai/pipeline/config.py`
