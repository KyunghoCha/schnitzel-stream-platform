#!/usr/bin/env bash
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
set -euo pipefail

PROFILE="${1:-base}"
MANAGER="${2:-auto}"
DRY_RUN="${3:-}"

if [[ ! -d "src" ]]; then
  echo "Error: src directory not found. Run from project root." >&2
  exit 1
fi

export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:${PYTHONPATH}}"
echo "PYTHONPATH=${PYTHONPATH}"
echo "profile=${PROFILE} manager=${MANAGER} dry_run=${DRY_RUN:-false}"

CMD=(python scripts/bootstrap_env.py --profile "${PROFILE}" --manager "${MANAGER}")
if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  CMD+=(--dry-run)
fi

echo "+ ${CMD[*]}"
"${CMD[@]}"

echo "Environment bootstrap complete."
echo "Try: python scripts/env_doctor.py --profile ${PROFILE} --strict --json"
