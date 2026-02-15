#!/usr/bin/env bash
# Docs: docs/progress/progress_log.md, docs/implementation/10-rtsp-stability/README.md, docs/implementation/90-packaging/README.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO="$ROOT/tests/play/2048246-hd_1920_1080_24fps.mp4"
LOG_DIR="/tmp/ai_pipeline_e2e_rtsp_stability_docker"
RTSP_URL="rtsp://127.0.0.1:8554/stream1"
MT_CFG="$LOG_DIR/mediamtx_docker.yml"
MT_DIR="/tmp/mediamtx"
MT_TAR="/tmp/mediamtx.tar.gz"
IMG_NAME="safety-ai"
CONTAINER_NAME="ai_rtsp_e2e"
BACKEND_PORT="${BACKEND_PORT:-18080}"
STRICT="${STRICT:-1}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$LOG_DIR"
export LOG_DIR

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  kill ${FFPID:-} ${MBPID:-} ${MTPID:-} >/dev/null 2>&1 || true
  wait ${FFPID:-} ${MBPID:-} ${MTPID:-} >/dev/null 2>&1 || true
}
trap cleanup EXIT

count_events() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import os

log_dir = Path(os.environ["LOG_DIR"])
mock_log = log_dir / "mock_backend.log"
if not mock_log.exists():
    print(0)
    raise SystemExit(0)
text = mock_log.read_text(encoding="utf-8", errors="ignore")
print(text.count("event="))
PY
}

wait_for_count() {
  local target="$1"
  local tries="${2:-30}"
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

is_port_in_use() {
  "$PYTHON_BIN" - <<'PY'
import socket
import os

port = int(os.environ["CHECK_PORT"])
s = socket.socket()
try:
    s.settimeout(0.2)
    s.connect(("127.0.0.1", port))
    print("1")
except Exception:
    print("0")
finally:
    s.close()
PY
}

get_free_port() {
  "$PYTHON_BIN" - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]
s.close()
print(port)
PY
}

main() {
  if ! docker image inspect "$IMG_NAME:latest" >/dev/null 2>&1; then
    docker build -t "$IMG_NAME" "$ROOT"
  fi

cat > "$MT_CFG" <<'EOF'
paths:
  stream1:
    source: publisher
EOF

if [ ! -x "$MT_DIR/mediamtx" ]; then
  curl -L -o "$MT_TAR" https://github.com/bluenviron/mediamtx/releases/download/v1.16.0/mediamtx_v1.16.0_linux_amd64.tar.gz
  mkdir -p "$MT_DIR"
  tar -xzf "$MT_TAR" -C "$MT_DIR"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Install ffmpeg on host before running RTSP E2E." >&2
  exit 1
fi

"$MT_DIR/mediamtx" "$MT_CFG" > "$LOG_DIR/mediamtx.log" 2>&1 &
MTPID=$!

sleep 1

CHECK_PORT="$BACKEND_PORT"
export CHECK_PORT
if [ "$(is_port_in_use)" = "1" ]; then
  BACKEND_PORT="$(get_free_port)"
fi

MOCK_BACKEND_PORT="$BACKEND_PORT" PYTHONPATH=src "$PYTHON_BIN" -m ai.pipeline.mock_backend > "$LOG_DIR/mock_backend.log" 2>&1 &
MBPID=$!

ffmpeg -re -stream_loop -1 -i "$VIDEO" -an -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -f rtsp "$RTSP_URL" > "$LOG_DIR/ffmpeg.log" 2>&1 &
FFPID=$!

sleep 3

docker run --rm --name "$CONTAINER_NAME" --network host \
  -e AI_EVENTS_POST_URL="http://127.0.0.1:${BACKEND_PORT}/api/events" \
  -e AI_EVENTS_SNAPSHOT_BASE_DIR="/data/snapshots" \
  -e AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX="/data/snapshots" \
  -v /tmp/snapshots:/data/snapshots \
  "$IMG_NAME" python -m schnitzel_stream --source-type rtsp --camera-id cam01 > "$LOG_DIR/pipeline_docker.log" 2>&1 &

wait_for_count 1 30 || true
COUNT_BEFORE="$(count_events)"

kill "$FFPID" >/dev/null 2>&1 || true
wait "$FFPID" >/dev/null 2>&1 || true
sleep 4

ffmpeg -re -stream_loop -1 -i "$VIDEO" -an -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -f rtsp "$RTSP_URL" > "$LOG_DIR/ffmpeg_restart.log" 2>&1 &
FFPID=$!

wait_for_count "$((COUNT_BEFORE + 1))" 30 || true
COUNT_AFTER="$(count_events)"

recovered="false"
if [ "$COUNT_AFTER" -gt "$COUNT_BEFORE" ]; then
  recovered="true"
fi
printf "count_before=%s\ncount_after=%s\nrecovered=%s\nbackend_port=%s\n" \
  "$COUNT_BEFORE" "$COUNT_AFTER" "$recovered" "$BACKEND_PORT" > "$LOG_DIR/status.txt"
  echo "Logs: $LOG_DIR"

  if [ "$STRICT" -eq 1 ] && [ "$recovered" != "true" ]; then
    echo "reconnect not recovered (STRICT=1)" >&2
    exit 1
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
