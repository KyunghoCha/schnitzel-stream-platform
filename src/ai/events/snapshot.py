# Docs: docs/implementation/40-snapshot/README.md
# src/ai/events/snapshot.py
from __future__ import annotations

# 스냅샷 저장 유틸
# - 저장 경로 생성
# - 실제 이미지 저장
# - public path 변환

from pathlib import Path
from datetime import datetime
import re
from typing import Any
import logging
import cv2

logger = logging.getLogger(__name__)


def build_snapshot_path(
    base_dir: str,
    site_id: str,
    camera_id: str,
    ts: str | None = None,
    track_id: int | None = None,
) -> Path:
    # 스냅샷 경로 생성
    # - base_dir/site_id/camera_id/ts(_track_id).jpg
    if ts is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    else:
        # 파일명 안전화를 위해 타임스탬프 정규화
        ts = re.sub(r"[^0-9A-Za-z_-]", "_", ts)
    name = f"{ts}"
    if track_id is not None:
        name = f"{name}_{track_id}"
    fname = f"{name}.jpg"
    return Path(base_dir) / site_id / camera_id / fname


def to_public_path(snapshot_path: Path, base_dir: str, public_prefix: str | None) -> str:
    # public_prefix가 있으면 base_dir을 public_prefix로 치환
    if public_prefix:
        try:
            rel = snapshot_path.relative_to(base_dir)
            return str(Path(public_prefix) / rel)
        except ValueError:
            return str(snapshot_path)
    return str(snapshot_path)


def save_snapshot(frame: Any, path: Path) -> Path | None:
    # 스냅샷 저장 (성공 시 경로 반환)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ok = cv2.imwrite(str(path), frame)
        if not ok:
            logger.warning("snapshot save failed: cv2.imwrite returned False")
            return None
        return path
    except OSError as exc:
        logger.warning("snapshot save failed: %s", exc)
        return None
