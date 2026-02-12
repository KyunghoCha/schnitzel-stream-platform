#!/usr/bin/env bash
# Docs: docs/ops/multi_camera_run.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="${CFG:-$ROOT/configs/cameras.yaml}"
LOG_DIR="${LOG_DIR:-/tmp/ai_pipeline_multi_cam_run}"
PID_DIR="${PID_DIR:-$LOG_DIR/pids}"
PYTHONPATH="${PYTHONPATH:-$ROOT/src}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

mkdir -p "$LOG_DIR" "$PID_DIR"

if [ ! -f "$CFG" ]; then
  echo "missing config: $CFG" >&2
  exit 1
fi

list_cameras() {
  python - <<'PY'
import sys
from pathlib import Path
from omegaconf import OmegaConf

cfg_path = Path(sys.argv[1])
data = OmegaConf.load(cfg_path)
cameras = data.get("cameras", [])
for cam in cameras:
    if not cam.get("enabled", True):
        continue
    cam_id = cam.get("id") or cam.get("camera_id")
    if cam_id:
        print(cam_id)
PY
}

CAMERA_IDS="${CAMERA_IDS:-$(list_cameras "$CFG")}"
if [ -z "$CAMERA_IDS" ]; then
  echo "no enabled cameras found in $CFG" >&2
  exit 1
fi

echo "log_dir=$LOG_DIR"
echo "pid_dir=$PID_DIR"
echo "cameras=$CAMERA_IDS"

for cam_id in $CAMERA_IDS; do
  pid_file="$PID_DIR/${cam_id}.pid"
  log_file="$LOG_DIR/${cam_id}.log"
  if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" >/dev/null 2>&1; then
    echo "already running: $cam_id (pid $(cat "$pid_file"))"
    continue
  fi

  PYTHONPATH="$PYTHONPATH" \
  python -m ai.pipeline --camera-id "$cam_id" $EXTRA_ARGS > "$log_file" 2>&1 &
  pid=$!
  echo "$pid" > "$pid_file"
  echo "started $cam_id pid=$pid log=$log_file"
done

echo "done"
