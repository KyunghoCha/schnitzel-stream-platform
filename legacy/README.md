# Legacy Runtime (Quarantined)

Last updated: 2026-02-15

## English

This folder contains the legacy AI/CCTV runtime (import path: `ai.*`).

Intent:
- Keep legacy code available during the deprecation window.
- Prevent new development from accreting onto the legacy surface.

### Location / Import Path

- Source code: `legacy/ai/**`
- Compatibility shim: `src/ai/__init__.py`
  - Keeps `import ai...` working by adding `legacy/` to `sys.path`.

### How To Run (Legacy v1 Graph)

```bash
python -m schnitzel_stream --graph configs/graphs/legacy_pipeline.yaml
```

### Deprecation

- v1 legacy runtime is deprecated (see Phase 4 `P4.3`).
- Removal is gated by the deprecation window (>= 90 days after `P4.3`).

SSOT: `docs/roadmap/execution_roadmap.md`, `docs/roadmap/legacy_decommission.md`

### Policy (Freeze)

- Allowed: security fixes, crash fixes, data-loss fixes.
- Not allowed: new features, new configuration keys, new plugin boundaries.

---

## 한국어

이 폴더는 레거시 AI/CCTV 런타임(import 경로: `ai.*`)을 포함합니다.

의도(Intent):
- deprecation window 동안 레거시 코드를 사용 가능 상태로 유지합니다.
- 신규 개발이 레거시 표면(legacy surface)에 계속 붙는 것을 방지합니다.

### 위치 / 임포트 경로

- 소스 코드: `legacy/ai/**`
- 호환 shim: `src/ai/__init__.py`
  - `legacy/`를 `sys.path`에 추가하여 `import ai...`가 동작하도록 유지합니다.

### 실행 방법 (Legacy v1 Graph)

```bash
python -m schnitzel_stream --graph configs/graphs/legacy_pipeline.yaml
```

### 디프리케이션

- v1 레거시 런타임은 deprecated 입니다(Phase 4 `P4.3` 참고).
- 삭제는 deprecation window에 의해 게이트됩니다(`P4.3` 이후 최소 90일).

SSOT: `docs/roadmap/execution_roadmap.md`, `docs/roadmap/legacy_decommission.md`

### 운영 정책 (Freeze)

- 허용: 보안/크래시/데이터 유실 버그 픽스
- 금지: 신규 기능, 신규 설정 키, 신규 플러그인 경계 추가
