from __future__ import annotations

# FrameSampler 단위 테스트

from ai.pipeline.sampler import FrameSampler


def test_sampler_interval_basic():
    sampler = FrameSampler(target_fps=10, source_fps=30)
    # 30/10=3 -> 0,3,6... 샘플
    assert sampler.should_sample(0)
    assert not sampler.should_sample(1)
    assert not sampler.should_sample(2)
    assert sampler.should_sample(3)


def test_sampler_source_fps_zero():
    sampler = FrameSampler(target_fps=10, source_fps=0)
    # source fps를 못 알 때는 모두 샘플
    assert sampler.should_sample(0)
    assert sampler.should_sample(1)
