#!/usr/bin/env bash
# Docs: docs/ops/multi_camera_run.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO="${VIDEO:-$ROOT/tests/play/2048246-hd_1920_1080_24fps.mp4}"
LOG_DIR="${LOG_DIR:-/tmp/ai_pipeline_multi_cam}"
RTSP_URL="${RTSP_URL:-rtsp://127.0.0.1:8554/stream1}"
BACKEND_PORT="${BACKEND_PORT:-18080}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}/api/events"
MT_CFG="/tmp/mediamtx.yml"
MT_DIR="/tmp/mediamtx"
MT_TAR="/tmp/mediamtx.tar.gz"

mkdir -p "$LOG_DIR"

cleanup() {
  kill ${FFPID:-} ${MBPID:-} ${MTPID:-} ${P1:-} ${P2:-} >/dev/null 2>&1 || true
  wait ${FFPID:-} ${MBPID:-} ${MTPID:-} ${P1:-} ${P2:-} >/dev/null 2>&1 || true
}
trap cleanup EXIT

cat > "$MT_CFG" <<'CFG'
paths:
  stream1:
    source: publisher
CFG

if [ ! -x "$MT_DIR/mediamtx" ]; then
  curl -L -o "$MT_TAR" https://github.com/bluenviron/mediamtx/releases/download/v1.16.0/mediamtx_v1.16.0_linux_amd64.tar.gz
  mkdir -p "$MT_DIR"
  tar -xzf "$MT_TAR" -C "$MT_DIR"
fi

"$MT_DIR/mediamtx" "$MT_CFG" > "$LOG_DIR/mediamtx.log" 2>&1 &
MTPID=$!

sleep 1

MOCK_BACKEND_PORT="$BACKEND_PORT" PYTHONPATH=src python -m ai.pipeline.mock_backend > "$LOG_DIR/mock_backend.log" 2>&1 &
MBPID=$!

ffmpeg -re -stream_loop -1 -i "$VIDEO" -an -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -f rtsp "$RTSP_URL" > "$LOG_DIR/ffmpeg.log" 2>&1 &
FFPID=$!

sleep 3

PYTHONPATH=src \
AI_EVENTS_POST_URL="$BACKEND_URL" \
AI_EVENTS_SNAPSHOT_BASE_DIR="/tmp/snapshots" \
AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX="/tmp/snapshots" \
python -m ai.pipeline --source-type rtsp --camera-id cam01 --max-events 5 > "$LOG_DIR/cam01.log" 2>&1 &
P1=$!

PYTHONPATH=src \
AI_EVENTS_POST_URL="$BACKEND_URL" \
AI_EVENTS_SNAPSHOT_BASE_DIR="/tmp/snapshots" \
AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX="/tmp/snapshots" \
python -m ai.pipeline --source-type file --camera-id cam02 --max-events 5 > "$LOG_DIR/cam02.log" 2>&1 &
P2=$!

wait $P1 $P2

echo "cam01_events=$(grep -c 'emit_ok=True' "$LOG_DIR/cam01.log" || true)" > "$LOG_DIR/status.txt"
echo "cam02_events=$(grep -c 'emit_ok=True' "$LOG_DIR/cam02.log" || true)" >> "$LOG_DIR/status.txt"
echo "Logs: $LOG_DIR"
