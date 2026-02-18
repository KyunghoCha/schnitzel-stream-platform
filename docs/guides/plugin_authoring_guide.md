# Plugin Authoring Guide

Last updated: 2026-02-18

## English

## Purpose

This guide defines the fastest path to create a new plugin in the platform runtime.

## Scaffold Command

```bash
python scripts/scaffold_plugin.py \
  --pack sensor \
  --kind node \
  --name ThresholdNode
```

Optional flags:
- `--module <module_name>`: override default module name derived from class name
- `--input-kinds <k1,k2,...>`: set `INPUT_KINDS` for node/sink
- `--output-kinds <k1,k2,...>`: set `OUTPUT_KINDS` for source/node
- `--register-export` (default): register generated class in `packs/<pack>/nodes/__init__.py`
- `--no-register-export`: skip export registration
- `--force`: overwrite existing generated files
- `--dry-run`: print deterministic file plan (`action=create|overwrite|conflict`) without writing files
- `--validate-generated`: run `compileall` + `python -m schnitzel_stream validate --graph ...` after generation

Validation contract:
- `--dry-run` + `--validate-generated` is blocked (`exit code 2`)
- generation/validation failure returns `exit code 1`
- validation failure keeps generated files for debugging

## Generated Files

For `--pack sensor --kind node --name ThresholdNode`:
- `src/schnitzel_stream/packs/sensor/nodes/threshold_node.py`
- `src/schnitzel_stream/packs/sensor/nodes/__init__.py` (auto export registration)
- `tests/unit/packs/sensor/nodes/test_threshold_node.py`
- `configs/graphs/dev_sensor_threshold_node_v2.yaml`

## Authoring Rules

1. Keep plugin behavior explicit via `StreamPacket` contract.
2. Add `Intent:` comments when behavior is deliberate/non-obvious.
3. Replace scaffold placeholder logic before production use.
4. Validate graph and run tests after implementation.
5. Keep export registration idempotent (`__init__.py` should not accumulate duplicates).

## Verify

```bash
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode --dry-run
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode --validate-generated
python scripts/plugin_contract_check.py --pack sensor --module threshold_node --class ThresholdNode --graph configs/graphs/dev_sensor_threshold_node_v2.yaml --strict --json
python -m schnitzel_stream validate --graph configs/graphs/dev_sensor_threshold_node_v2.yaml
python3 -m compileall -q src tests scripts
```

---

## 한국어

## 목적

이 가이드는 플랫폼 런타임에서 새 플러그인을 가장 빠르게 만드는 방법을 정의한다.

## 스캐폴드 명령

```bash
python scripts/scaffold_plugin.py \
  --pack sensor \
  --kind node \
  --name ThresholdNode
```

선택 옵션:
- `--module <module_name>`: 클래스명 기반 기본 모듈명을 직접 지정
- `--input-kinds <k1,k2,...>`: node/sink의 `INPUT_KINDS` 지정
- `--output-kinds <k1,k2,...>`: source/node의 `OUTPUT_KINDS` 지정
- `--register-export` (기본): 생성 클래스를 `packs/<pack>/nodes/__init__.py`에 자동 등록
- `--no-register-export`: 자동 export 등록 생략
- `--force`: 기존 생성 파일 덮어쓰기
- `--dry-run`: 파일을 생성하지 않고 `action=create|overwrite|conflict` 계획만 출력
- `--validate-generated`: 생성 직후 `compileall` + 그래프 validate를 자동 실행

검증 계약:
- `--dry-run` + `--validate-generated` 동시 사용은 차단(`exit code 2`)
- 생성/검증 실패는 `exit code 1` 반환
- 검증 실패 시 생성 파일은 디버깅을 위해 보존

## 생성 파일

예: `--pack sensor --kind node --name ThresholdNode`
- `src/schnitzel_stream/packs/sensor/nodes/threshold_node.py`
- `src/schnitzel_stream/packs/sensor/nodes/__init__.py` (자동 export 등록)
- `tests/unit/packs/sensor/nodes/test_threshold_node.py`
- `configs/graphs/dev_sensor_threshold_node_v2.yaml`

## 작성 규칙

1. `StreamPacket` 계약 기반으로 플러그인 동작을 명확히 유지한다.
2. 의도적/비자명 동작에는 `Intent:` 주석을 남긴다.
3. 스캐폴드의 placeholder 로직은 실제 구현으로 교체한다.
4. 구현 후 그래프 검증과 테스트를 실행한다.
5. export 등록은 idempotent하게 유지한다(`__init__.py` 중복 라인 금지).

## 검증

```bash
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode --dry-run
python scripts/scaffold_plugin.py --pack sensor --kind node --name ThresholdNode --validate-generated
python scripts/plugin_contract_check.py --pack sensor --module threshold_node --class ThresholdNode --graph configs/graphs/dev_sensor_threshold_node_v2.yaml --strict --json
python -m schnitzel_stream validate --graph configs/graphs/dev_sensor_threshold_node_v2.yaml
python3 -m compileall -q src tests scripts
```
