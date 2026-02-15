# Docs: docs/legacy/specs/legacy_pipeline_spec.md
from __future__ import annotations

# 프레임 샘플러
# - 원본 FPS를 목표 FPS로 다운샘플링

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameSampler:
    target_fps: int
    source_fps: float

    def __post_init__(self) -> None:
        # 샘플링 간격 계산
        if self.target_fps <= 0:
            logger.warning("target_fps=%d is invalid, clamped to 1", self.target_fps)
            self.target_fps = 1

        if self.source_fps <= 0:
            self._ratio = None
        else:
            self._ratio = float(self.target_fps) / float(self.source_fps)

    def should_sample(self, frame_idx: int) -> bool:
        # 현재 프레임이 샘플링 대상인지 결정
        if self._ratio is None:
            return True
        if frame_idx == 0:
            return True
        prev = int((frame_idx - 1) * self._ratio)
        curr = int(frame_idx * self._ratio)
        return curr > prev
