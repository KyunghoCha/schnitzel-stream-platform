#!/usr/bin/env bash
# Docs: docs/ops/command_reference.md, docs/guides/local_console_quickstart.md
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./setup_env.sh [--profile <base|console|yolo>] [--manager <auto|conda|pip>] [--dry-run] [--skip-doctor]

Legacy compatibility (deprecated, one-cycle):
  ./setup_env.sh [profile] [manager] [--dry-run]
USAGE
}

PROFILE="base"
MANAGER="auto"
DRY_RUN="false"
SKIP_DOCTOR="false"
POSITIONAL_USED="false"

if [[ $# -gt 0 && "${1#-}" == "$1" ]]; then
  POSITIONAL_USED="true"
  PROFILE="${1:-base}"
  shift || true
  if [[ $# -gt 0 && "${1#-}" == "$1" ]]; then
    MANAGER="${1:-auto}"
    shift || true
  fi
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || { echo "Error: --profile requires a value" >&2; usage; exit 2; }
      PROFILE="$2"
      shift 2
      ;;
    --manager)
      [[ $# -ge 2 ]] || { echo "Error: --manager requires a value" >&2; usage; exit 2; }
      MANAGER="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --skip-doctor)
      SKIP_DOCTOR="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "${POSITIONAL_USED}" == "true" ]]; then
  echo "Warning: positional setup_env.sh arguments are deprecated; use --profile/--manager flags." >&2
fi

if [[ ! -d "src" ]]; then
  echo "Error: src directory not found. Run from project root." >&2
  exit 1
fi

export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:${PYTHONPATH}}"
echo "profile=${PROFILE}"
echo "manager=${MANAGER}"
echo "dry_run=${DRY_RUN}"
echo "skip_doctor=${SKIP_DOCTOR}"

PY_EXE="$(command -v python || true)"
if [[ -z "${PY_EXE}" ]]; then
  PY_EXE="$(command -v python3 || true)"
fi
if [[ -z "${PY_EXE}" ]]; then
  echo "Error: python/python3 executable not found in PATH." >&2
  exit 1
fi

CMD=("${PY_EXE}" scripts/bootstrap_env.py --profile "${PROFILE}" --manager "${MANAGER}")
if [[ "${DRY_RUN}" == "true" ]]; then
  CMD+=(--dry-run)
fi
if [[ "${SKIP_DOCTOR}" == "true" ]]; then
  CMD+=(--skip-doctor)
fi

echo "+ ${CMD[*]}"
"${CMD[@]}"

echo "Environment bootstrap complete."
if [[ "${SKIP_DOCTOR}" == "true" ]]; then
  echo "next=${PY_EXE} scripts/env_doctor.py --profile ${PROFILE} --strict --json"
else
  echo "next=${PY_EXE} scripts/stream_console.py up --allow-local-mutations"
fi
