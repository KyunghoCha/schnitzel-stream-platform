#!/usr/bin/env bash
# Docs: docs/progress/progress_log.md, docs/implementation/10-rtsp-stability/README.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO="$ROOT/tests/play/2048246-hd_1920_1080_24fps.mp4"
CFG="$ROOT/configs/cameras.yaml"
BACKUP="/tmp/cameras.yaml.bak"
LOG_DIR="/tmp/ai_pipeline_e2e_rtsp_stability"
RTSP_URL="rtsp://127.0.0.1:8554/stream1"
BACKEND_PORT="${BACKEND_PORT:-18080}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}/api/events"
STRICT="${STRICT:-1}"
MT_CFG="/tmp/mediamtx.yml"
MT_DIR="/tmp/mediamtx"
MT_TAR="/tmp/mediamtx.tar.gz"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$LOG_DIR"
export LOG_DIR
cp "$CFG" "$BACKUP"

cleanup() {
  kill ${FFPID:-} ${MBPID:-} ${MTPID:-} ${PPID_RTSP:-} >/dev/null 2>&1 || true
  wait ${FFPID:-} ${MBPID:-} ${MTPID:-} ${PPID_RTSP:-} >/dev/null 2>&1 || true
  if [ -f "$BACKUP" ]; then
    cp "$BACKUP" "$CFG"
  fi
}
trap cleanup EXIT

count_events() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import os

log_dir = Path(os.environ["LOG_DIR"])
mock_log = log_dir / "mock_backend.log"
pipe_log = log_dir / "pipeline.log"
if mock_log.exists():
    target = mock_log
    pattern = "event="
else:
    target = pipe_log
    pattern = "emit_ok=True"
if not target.exists():
    print(0)
    raise SystemExit(0)
text = target.read_text(encoding="utf-8", errors="ignore")
print(text.count(pattern))
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

"$PYTHON_BIN" - <<PY
from omegaconf import OmegaConf

p = "$CFG"
cfg = OmegaConf.load(p)
cams = cfg.get("cameras", [])
for cam in cams:
    src = cam.get("source", {})
    if cam.get("id") == "cam01" or src.get("type") == "rtsp":
        src["type"] = "rtsp"
        src["url"] = "$RTSP_URL"
        cam["source"] = src
        break
cfg["cameras"] = cams
OmegaConf.save(cfg, p)
PY

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

"$MT_DIR/mediamtx" "$MT_CFG" > "$LOG_DIR/mediamtx.log" 2>&1 &
MTPID=$!

sleep 1

CHECK_PORT="$BACKEND_PORT"
export CHECK_PORT
if [ "$(is_port_in_use)" = "1" ]; then
  BACKEND_PORT="$(get_free_port)"
  BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}/api/events"
fi

MOCK_BACKEND_PORT="$BACKEND_PORT" PYTHONPATH=src "$PYTHON_BIN" -m ai.pipeline.mock_backend > "$LOG_DIR/mock_backend.log" 2>&1 &
MBPID=$!

ffmpeg -re -stream_loop -1 -i "$VIDEO" -an -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -f rtsp "$RTSP_URL" > "$LOG_DIR/ffmpeg.log" 2>&1 &
FFPID=$!

sleep 3

PYTHONPATH=src \
AI_EVENTS_POST_URL="$BACKEND_URL" \
AI_EVENTS_SNAPSHOT_BASE_DIR="/tmp/snapshots" \
AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX="/tmp/snapshots" \
"$PYTHON_BIN" -m schnitzel_stream --source-type rtsp --camera-id cam01 > "$LOG_DIR/pipeline.log" 2>&1 &
PPID_RTSP=$!

wait_for_count 1 30 || true
COUNT_BEFORE="$(count_events)"

kill $FFPID >/dev/null 2>&1 || true
wait $FFPID >/dev/null 2>&1 || true
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
