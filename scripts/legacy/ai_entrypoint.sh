#!/usr/bin/env bash
# Docs: docs/implementation/90-packaging/entrypoint/spec.md
set -euo pipefail

# 기본 엔트리포인트
# - ENV 오버라이드 사용 가능
# - 인자 전달 시 그대로 실행

if [ "$#" -eq 0 ]; then
  exec python -m ai.pipeline --dry-run
else
  exec "$@"
fi
