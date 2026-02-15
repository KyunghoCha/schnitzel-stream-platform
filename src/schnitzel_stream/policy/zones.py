from __future__ import annotations

"""
DEPRECATED: vision policies moved to `schnitzel_stream.packs.vision.policy`.

Kept as a compatibility shim for older imports that reference `schnitzel_stream.policy.zones`.
"""

from schnitzel_stream.packs.vision.policy.zones import ZoneCache, ZoneEvaluator, evaluate_zones, fetch_zones_from_api, load_zones, load_zones_from_file

__all__ = [
    "ZoneCache",
    "ZoneEvaluator",
    "evaluate_zones",
    "fetch_zones_from_api",
    "load_zones",
    "load_zones_from_file",
]

