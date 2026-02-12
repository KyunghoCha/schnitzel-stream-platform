#!/usr/bin/env bash
# Docs: docs/implementation/10-rtsp-stability/README.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO="${VIDEO:-$ROOT/tests/play/2048246-hd_1920_1080_24fps.mp4}"
LOG_DIR="${LOG_DIR:-/tmp/ai_pipeline_e2e_rtsp_reconnect}"
RTSP_URL="${RTSP_URL:-rtsp://127.0.0.1:8554/stream1}"
BACKEND_PORT="${BACKEND_PORT:-18080}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}/api/events"
MT_CFG="/tmp/mediamtx.yml"
MT_DIR="/tmp/mediamtx"
MT_TAR="/tmp/mediamtx.tar.gz"
RECONNECT_CYCLES="${RECONNECT_CYCLES:-1}"
MAX_EVENTS="${MAX_EVENTS:-10}"

mkdir -p "$LOG_DIR"

cleanup() {
  kill ${FFPID:-} ${MBPID:-} ${MTPID:-} ${PPID_RTSP:-} >/dev/null 2>&1 || true
  wait ${FFPID:-} ${MBPID:-} ${MTPID:-} ${PPID_RTSP:-} >/dev/null 2>&1 || true
}
trap cleanup EXIT

count_events() {
  local target_log pattern
  target_log="$LOG_DIR/mock_backend.log"
  pattern="event="
  if [ ! -f "$target_log" ]; then
    echo 0
    return
  fi
  local count
  if command -v rg >/dev/null 2>&1; then
    count="$(rg -c "$pattern" "$target_log" 2>/dev/null | tail -n 1)"
  else
    count="$(grep -c "$pattern" "$target_log" 2>/dev/null || true)"
  fi
  count="${count##*:}"
  count="$(printf "%s" "$count" | tr -cd '0-9')"
  if [ -z "$count" ]; then
    count=0
  fi
  echo "$count"
}

wait_for_count() {
  local target="$1"
  local tries="${2:-40}"
  for _ in $(seq 1 "$tries"); do
    local count
    count="$(count_events)"
    if [ "$count" -ge "$target" ]; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

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
python -m ai.pipeline --source-type rtsp --camera-id cam01 --max-events "$MAX_EVENTS" > "$LOG_DIR/pipeline.log" 2>&1 &
PPID_RTSP=$!

wait_for_count 2 20 || true
COUNT_START="$(count_events)"
COUNT_BEFORE="${COUNT_START}"

for i in $(seq 1 "$RECONNECT_CYCLES"); do
  kill $FFPID >/dev/null 2>&1 || true
  wait $FFPID >/dev/null 2>&1 || true
  sleep 3

  ffmpeg -re -stream_loop -1 -i "$VIDEO" -an -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -f rtsp "$RTSP_URL" > "$LOG_DIR/ffmpeg_restart_${i}.log" 2>&1 &
  FFPID=$!

  wait_for_count "$((COUNT_START + 1))" 20 || true
  COUNT_START="$(count_events)"
  sleep 1

done

COUNT_END="$(count_events)"

printf "reconnect_cycles=%s\ncount_before=%s\ncount_after=%s\n" "$RECONNECT_CYCLES" "$COUNT_BEFORE" "$COUNT_END" > "$LOG_DIR/status.txt"
echo "Logs: $LOG_DIR"
