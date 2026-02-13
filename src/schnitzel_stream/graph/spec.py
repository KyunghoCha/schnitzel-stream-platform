from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf


@dataclass(frozen=True)
class GraphSpec:
    """Graph specification (Phase 0 minimal).

    Intent:
    - Phase 0 uses a "job" indirection instead of a full DAG runtime.
    - This keeps the migration reversible while SSOT is still evolving.
    """

    version: int
    job: str
    config: dict[str, Any]


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    return {}


def load_graph_spec(path: str | Path) -> GraphSpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"graph spec not found: {p}")

    data = OmegaConf.load(p)
    cont = OmegaConf.to_container(data, resolve=True)
    if not isinstance(cont, dict):
        raise ValueError(f"graph spec top-level must be a mapping: {p}")

    version_raw = cont.get("version", 1)
    try:
        version = int(version_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"graph spec version must be int: {p}") from exc

    job = cont.get("job")
    if not isinstance(job, str) or not job.strip():
        raise ValueError(f"graph spec requires 'job' (module:Name): {p}")

    config = _as_dict(cont.get("config"))
    return GraphSpec(version=version, job=job.strip(), config=config)

