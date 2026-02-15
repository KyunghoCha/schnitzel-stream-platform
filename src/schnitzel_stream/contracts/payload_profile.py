from __future__ import annotations

"""
Payload profile contract (P10.5 draft).

Intent:
- Keep payload portability explicit while preserving compatibility with existing node contracts.
- Provide a small profile vocabulary that validators can reason about.
"""

PROFILE_INPROC_ANY = "inproc_any"
PROFILE_JSON_PORTABLE = "json_portable"
PROFILE_REF_PORTABLE = "ref_portable"

_ALLOWED_PROFILES = {
    PROFILE_INPROC_ANY,
    PROFILE_JSON_PORTABLE,
    PROFILE_REF_PORTABLE,
}

# Source profile -> accepted destination input profiles.
_PROFILE_COMPAT: dict[str, set[str]] = {
    PROFILE_INPROC_ANY: {PROFILE_INPROC_ANY},
    PROFILE_JSON_PORTABLE: {PROFILE_INPROC_ANY, PROFILE_JSON_PORTABLE},
    PROFILE_REF_PORTABLE: {PROFILE_INPROC_ANY, PROFILE_JSON_PORTABLE, PROFILE_REF_PORTABLE},
}


def normalize_profile(raw: object | None) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValueError("payload profile must be a string")
    val = raw.strip().lower()
    if not val:
        return None
    if val not in _ALLOWED_PROFILES:
        raise ValueError(f"unsupported payload profile: {raw!r}")
    return val


def is_profile_compatible(source_profile: str, dest_input_profile: str) -> bool:
    src = normalize_profile(source_profile)
    dst = normalize_profile(dest_input_profile)
    if src is None or dst is None:
        raise ValueError("source_profile and dest_input_profile must be non-empty supported profiles")
    return dst in _PROFILE_COMPAT[src]
