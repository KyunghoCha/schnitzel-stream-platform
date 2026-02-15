#!/usr/bin/env bash
# Docs: legacy/docs/legacy/ops/multi_camera_run.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${LOG_DIR:-/tmp/ai_pipeline_multi_cam_run}"
PID_DIR="${PID_DIR:-$LOG_DIR/pids}"

if [ ! -d "$PID_DIR" ]; then
  echo "pid_dir not found: $PID_DIR"
  exit 0
fi

stopped=0
for pid_file in "$PID_DIR"/*.pid; do
  [ -e "$pid_file" ] || continue
  pid="$(cat "$pid_file")"
  cam_id="$(basename "$pid_file" .pid)"
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    echo "stopped $cam_id pid=$pid"
    stopped=$((stopped + 1))
  else
    echo "stale pid for $cam_id (pid $pid)"
  fi
  rm -f "$pid_file"
done

echo "stopped_count=$stopped"
