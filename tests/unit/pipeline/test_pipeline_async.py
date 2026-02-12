from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

from ai.pipeline.core import Pipeline, PipelineContext
from ai.pipeline.sampler import FrameSampler


# -- test helpers -----------------------------------------------------------


class _FakeLiveSource:
    supports_reconnect = False

    def __init__(self, n_frames: int = 3):
        self._count = 0
        self._n_frames = n_frames

    @property
    def is_live(self) -> bool:
        return True

    def read(self):
        if self._count >= self._n_frames:
            return False, None
        self._count += 1
        return True, f"frame-{self._count}"

    def release(self):
        return None

    def fps(self) -> float:
        return 30.0


class _FakeFileSource:
    supports_reconnect = False

    def __init__(self, n_frames: int = 3):
        self._count = 0
        self._n_frames = n_frames

    @property
    def is_live(self) -> bool:
        return False

    def read(self):
        if self._count >= self._n_frames:
            return False, None
        self._count += 1
        return True, f"frame-{self._count}"

    def release(self):
        return None

    def fps(self) -> float:
        return 10.0


class _SingleBuilder:
    def build(self, frame_idx: int, frame: Any) -> list[dict[str, Any]]:
        return [{"event_id": f"e{frame_idx}", "camera_id": "cam01", "event_type": "ZONE_INTRUSION"}]


class _CollectEmitter:
    def __init__(self):
        self.payloads: list[dict[str, Any]] = []

    def emit(self, payload: dict[str, Any]) -> bool:
        self.payloads.append(payload)
        return True

    def close(self) -> None:
        pass


# -- tests ------------------------------------------------------------------


def test_live_source_uses_processor():
    """is_live=True일 때 FrameProcessor(비동기 경로)를 사용한다."""
    emitter = _CollectEmitter()
    ctx = PipelineContext(
        source=_FakeLiveSource(n_frames=3),
        sampler=FrameSampler(target_fps=30, source_fps=30),
        event_builder=_SingleBuilder(),
        emitter=emitter,
    )

    with patch("ai.pipeline.core.FrameProcessor") as mock_proc_cls:
        mock_proc = mock_proc_cls.return_value
        mock_proc.emitted = 0
        mock_proc.get_results.return_value = []

        Pipeline(ctx).run()

        # FrameProcessor가 생성되었는지 확인
        mock_proc_cls.assert_called_once()
        # submit이 호출되었는지 확인
        assert mock_proc.submit.call_count >= 1
        # stop이 호출되었는지 확인
        mock_proc.stop.assert_called_once()


def test_file_source_uses_sync():
    """is_live=False일 때 동기 경로(_process_frame)를 사용한다."""
    emitter = _CollectEmitter()
    ctx = PipelineContext(
        source=_FakeFileSource(n_frames=2),
        sampler=FrameSampler(target_fps=10, source_fps=10),
        event_builder=_SingleBuilder(),
        emitter=emitter,
    )

    with patch("ai.pipeline.core.FrameProcessor") as mock_proc_cls:
        Pipeline(ctx).run()

        # FrameProcessor가 생성되지 않아야 함
        mock_proc_cls.assert_not_called()

    # 동기 처리로 emitter에 직접 도달
    assert len(emitter.payloads) == 2
    assert emitter.payloads[0]["event_id"] == "e0"
    assert emitter.payloads[1]["event_id"] == "e1"
