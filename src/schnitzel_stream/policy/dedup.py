from __future__ import annotations

"""
DEPRECATED: vision policies moved to `schnitzel_stream.packs.vision.policy`.

Kept as a compatibility shim for older imports that reference `schnitzel_stream.policy.dedup`.
"""

from schnitzel_stream.packs.vision.policy.dedup import CooldownStore, DedupController, build_dedup_key

__all__ = ["CooldownStore", "DedupController", "build_dedup_key"]

