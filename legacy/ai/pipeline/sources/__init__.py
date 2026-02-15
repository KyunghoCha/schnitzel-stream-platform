# Docs: docs/legacy/specs/legacy_pipeline_spec.md
"""
프레임 소스 패키지

사용 가능한 소스:
- FileSource: MP4 파일
- RtspSource: RTSP 스트림 (자동 재연결)
- WebcamSource: 웹캠 (device index)
- ThreadedSource: 라이브 소스 스레드 분리 래퍼
- load_frame_source: 커스텀 소스 플러그인 로더(module:ClassName)

Example:
    from ai.pipeline.sources import FileSource, RtspSource, WebcamSource, ThreadedSource
"""
from __future__ import annotations

from ai.pipeline.sources.protocol import FrameSource
from ai.pipeline.sources.file import FileSource
from ai.pipeline.sources.rtsp import RtspSource
from ai.pipeline.sources.webcam import WebcamSource
from ai.pipeline.sources.threaded import ThreadedSource
from ai.pipeline.sources.loader import load_frame_source

__all__ = [
    "FrameSource",
    "FileSource",
    "RtspSource",
    "WebcamSource",
    "ThreadedSource",
    "load_frame_source",
]
