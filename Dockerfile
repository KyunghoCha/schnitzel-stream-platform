# AI pipeline container
FROM python:3.11.11-slim

WORKDIR /app

# System deps for opencv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps (minimal)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

ENV PYTHONPATH=/app/src

# Snapshot base dir (must be writable)
ENV AI_EVENTS_SNAPSHOT_BASE_DIR=/data/snapshots
ENV AI_EVENTS_SNAPSHOT_PUBLIC_PREFIX=/data/snapshots

RUN mkdir -p /data/snapshots \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --no-create-home appuser \
    && chown -R appuser:appuser /data/snapshots

USER appuser

CMD ["python", "-m", "ai.pipeline"]
