from __future__ import annotations

"""
Zone evaluation policy (ported from legacy).

Intent:
- Phase 4 legacy removal: port `ai.rules.zones` into the platform namespace.
- Keep behavior compatible with the legacy implementation to make parity/cutover measurable.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import threading
from typing import Any
from urllib import error, request

from omegaconf import OmegaConf

from schnitzel_stream.utils.urls import mask_url

logger = logging.getLogger(__name__)


def _now_ts() -> float:
    # cache TTL helper (UTC timestamp)
    return datetime.now(timezone.utc).timestamp()


def point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    """Return True if a point is inside the polygon (odd-even rule).

    Notes:
    - polygon: [[x, y], ...]
    - points on the boundary are treated as inside.
    """

    if len(polygon) < 3:
        return False

    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]

        # On a horizontal boundary line
        if (
            math.isclose(y1, y2, abs_tol=1e-9)
            and math.isclose(y, y1, abs_tol=1e-9)
            and min(x1, x2) <= x <= max(x1, x2)
        ):
            return True

        intersects = (y1 > y) != (y2 > y)
        if intersects:
            x_at_y = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
            if math.isclose(x_at_y, x, abs_tol=1e-9):
                return True  # boundary
            if x_at_y > x:
                inside = not inside
    return inside


def rule_point_from_bbox(event_type: str, bbox: dict[str, Any], rule_map: dict[str, str]) -> tuple[float, float] | None:
    """Compute rule point based on event_type-specific policy."""

    if not bbox:
        return None
    x1, y1, x2, y2 = bbox.get("x1"), bbox.get("y1"), bbox.get("x2"), bbox.get("y2")
    if None in (x1, y1, x2, y2):
        return None

    rule = rule_map.get(event_type, "bottom_center")
    if rule == "bbox_center":
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
    return ((x1 + x2) / 2.0, float(y2))


def evaluate_zones(
    event_type: str,
    bbox: dict[str, Any],
    zones: list[dict[str, Any]],
    rule_map: dict[str, str],
) -> dict[str, Any]:
    """Evaluate zone 'inside' based on rule_point and zone polygons."""

    point = rule_point_from_bbox(event_type, bbox, rule_map)
    if point is None:
        return {"zone_id": "", "inside": False}

    for zone in zones:
        if not zone.get("enabled", True):
            continue
        polygon = zone.get("polygon")
        if not isinstance(polygon, list) or len(polygon) < 3:
            logger.warning(
                "invalid zone polygon, skipping",
                extra={"error_code": "ZONES_INVALID_POLYGON", "zone_id": zone.get("zone_id", "")},
            )
            continue
        if point_in_polygon(point, polygon):
            return {"zone_id": zone.get("zone_id", ""), "inside": True}

    return {"zone_id": "", "inside": False}


def _load_yaml(path: Path) -> list[dict[str, Any]]:
    # Support: list or {zones: [...]}
    data = OmegaConf.load(path)
    cont = OmegaConf.to_container(data, resolve=True)
    if isinstance(cont, list):
        return cont
    if isinstance(cont, dict):
        zones = cont.get("zones", [])
        if isinstance(zones, list):
            return zones
    return []


def load_zones_from_file(path: str) -> list[dict[str, Any]]:
    """Load zones from a json/yaml file."""

    fpath = Path(path)
    if not fpath.exists():
        return []
    if fpath.suffix.lower() in (".yaml", ".yml"):
        return _load_yaml(fpath)
    if fpath.suffix.lower() == ".json":
        data = json.loads(fpath.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            zones = data.get("zones", [])
            if isinstance(zones, list):
                return zones
        return []
    return []


def fetch_zones_from_api(
    base_url: str,
    path_template: str,
    site_id: str,
    camera_id: str,
    timeout_sec: float,
) -> list[dict[str, Any]] | None:
    """Fetch zones from an HTTP API (GET)."""

    url = base_url.rstrip("/") + path_template.format(site_id=site_id, camera_id=camera_id)
    try:
        req = request.Request(url, method="GET")
        with request.urlopen(req, timeout=timeout_sec) as resp:
            data = resp.read()
            out = json.loads(data.decode("utf-8"))
            return out if isinstance(out, list) else None
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning(
            "zones fetch failed: %s",
            exc,
            extra={"error_code": "ZONES_FETCH_FAILED", "url": mask_url(url)},
        )
        return None


@dataclass
class ZoneCache:
    """Simple in-memory TTL cache for zones."""

    ttl_sec: float
    error_backoff_sec: float = 5.0
    max_failures: int = 3
    _zones: list[dict[str, Any]] | None = field(default=None, init=False, repr=False)
    _last_fetch_ts: float = field(default=0.0, init=False, repr=False)
    _failures: int = field(default=0, init=False, repr=False)
    _error_until_ts: float = field(default=0.0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def get(self) -> list[dict[str, Any]] | None:
        with self._lock:
            if self._zones is None:
                return None
            if _now_ts() - self._last_fetch_ts > self.ttl_sec:
                return None
            return list(self._zones)

    def get_stale(self) -> list[dict[str, Any]]:
        """Return cached zones without TTL checks (empty list if missing)."""

        with self._lock:
            if self._zones is None:
                return []
            return list(self._zones)

    def should_fetch(self) -> bool:
        with self._lock:
            if self._error_until_ts <= 0:
                return True
            return _now_ts() >= self._error_until_ts

    def set(self, zones: list[dict[str, Any]]) -> None:
        with self._lock:
            self._zones = list(zones)
            self._last_fetch_ts = _now_ts()
            self._failures = 0
            self._error_until_ts = 0.0

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self.error_backoff_sec <= 0:
                return
            threshold = max(1, int(self.max_failures))
            if self._failures >= threshold:
                self._error_until_ts = _now_ts() + self.error_backoff_sec
                self._failures = 0


@dataclass
class ZoneEvaluator:
    """Zone evaluation with file/api loading and caching.

    Intent:
    - Keep API fetching off the hot path by using cached zones and refreshing async.
    - Mirror legacy behavior so parity tests can compare old vs new.
    """

    source: str
    site_id: str
    camera_id: str
    rule_map: dict[str, str]
    api_cfg: dict[str, Any] | None = None
    file_path: str | None = None
    cache_ttl_sec: float = 30.0
    _cache: ZoneCache | None = field(default=None, init=False, repr=False)
    _refresh_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _refresh_inflight: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.source in ("api", "file") and self.cache_ttl_sec > 0:
            error_backoff_sec = 0.0
            max_failures = 3
            if self.api_cfg:
                error_backoff_sec = float(self.api_cfg.get("error_backoff_sec", 5.0))
                max_failures = int(self.api_cfg.get("max_failures", 3))
            self._cache = ZoneCache(self.cache_ttl_sec, error_backoff_sec, max_failures)

    def apply(self, payload: dict[str, Any]) -> dict[str, Any]:
        event_type = payload.get("event_type", "")
        bbox = payload.get("bbox", {})
        zones = self._load_for_apply()
        if zones:
            payload["zone"] = evaluate_zones(str(event_type), dict(bbox) if isinstance(bbox, dict) else {}, zones, self.rule_map)
        else:
            payload["zone"] = {"zone_id": "", "inside": False}
        return payload

    def _load_for_apply(self) -> list[dict[str, Any]]:
        if self.source != "api":
            return load_zones(
                source=self.source,
                site_id=self.site_id,
                camera_id=self.camera_id,
                api_cfg=self.api_cfg,
                file_path=self.file_path,
                cache=self._cache,
            )

        # Intent: API-based lookup must not block the inference path.
        # apply() uses stale cache immediately; refresh happens in background.
        zones = self._cache.get_stale() if self._cache is not None else []
        self._refresh_api_async_if_needed()
        return zones

    def _refresh_api_async_if_needed(self) -> None:
        if self.api_cfg is None or self._cache is None:
            return
        if self._cache.get() is not None:
            return
        if not self._cache.should_fetch():
            return

        with self._refresh_lock:
            if self._refresh_inflight:
                return
            self._refresh_inflight = True

        threading.Thread(
            target=self._refresh_api_once,
            name=f"zone-refresh-{self.camera_id}",
            daemon=True,
        ).start()

    def _refresh_api_once(self) -> None:
        try:
            if self.api_cfg is None or self._cache is None:
                return
            zones = fetch_zones_from_api(
                base_url=self.api_cfg.get("base_url", ""),
                path_template=self.api_cfg.get("get_path_template", ""),
                site_id=self.site_id,
                camera_id=self.camera_id,
                timeout_sec=float(self.api_cfg.get("timeout_sec", 3)),
            )
            if zones is None:
                self._cache.record_failure()
                return
            self._cache.set(zones)
        finally:
            with self._refresh_lock:
                self._refresh_inflight = False


def load_zones(
    *,
    source: str,
    site_id: str,
    camera_id: str,
    api_cfg: dict[str, Any] | None,
    file_path: str | None,
    cache: ZoneCache | None = None,
) -> list[dict[str, Any]]:
    """Load zones from the given source (file/api)."""

    if source == "file":
        if not file_path:
            return []
        cached = cache.get() if cache else None
        if cached is not None:
            return cached
        zones = load_zones_from_file(file_path)
        if cache:
            cache.set(zones)
        return zones

    if source == "api":
        cached = cache.get() if cache else None
        if cached is not None:
            return cached
        if cache and not cache.should_fetch():
            return cache.get_stale()
        if not api_cfg:
            return []
        zones = fetch_zones_from_api(
            base_url=api_cfg.get("base_url", ""),
            path_template=api_cfg.get("get_path_template", ""),
            site_id=site_id,
            camera_id=camera_id,
            timeout_sec=float(api_cfg.get("timeout_sec", 3)),
        )
        if zones is None:
            if cache:
                cache.record_failure()
            stale = cache.get_stale() if cache else []
            return stale if stale else []
        if cache:
            cache.set(zones)
        return zones

    return []

