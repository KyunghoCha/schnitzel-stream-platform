from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any, Callable


def _parse_prefixes(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    parts = [p.strip() for p in raw.split(",")]
    return tuple(p for p in parts if p)


def _is_allowed_module(module_path: str, allowed_prefixes: tuple[str, ...]) -> bool:
    if not allowed_prefixes:
        return True
    return any(module_path.startswith(prefix) for prefix in allowed_prefixes)


def _module_from_plugin_path(path: str) -> str | None:
    if ":" not in path:
        return None
    module_path = path.split(":", 1)[0].strip()
    return module_path or None


@dataclass(frozen=True)
class PluginPolicy:
    """Plugin loading policy (prod-safe by default)."""

    allowed_prefixes: tuple[str, ...]
    allow_all: bool = False

    @classmethod
    def from_env(cls) -> PluginPolicy:
        # Default allowlist: repo-owned namespaces only.
        default_prefixes = ("schnitzel_stream.", "ai.")
        raw = os.environ.get("ALLOWED_PLUGIN_PREFIXES", "")
        prefixes = _parse_prefixes(raw) or default_prefixes
        allow_all = os.environ.get("ALLOW_ALL_PLUGINS", "").strip().lower() in ("1", "true", "yes")
        return cls(allowed_prefixes=prefixes, allow_all=allow_all)

    def is_allowed_module(self, module_path: str) -> bool:
        if self.allow_all:
            return True
        return _is_allowed_module(module_path, self.allowed_prefixes)

    def ensure_path_allowed(self, path: str) -> None:
        """Raise PermissionError if the `module:Name` path violates policy."""
        module_path = _module_from_plugin_path(path)
        if not module_path:
            # Path structure validation happens elsewhere; policy enforces prefix allowlist only.
            return
        if self.is_allowed_module(module_path):
            return
        raise PermissionError(
            f"plugin module is not allowed: {module_path}. "
            "Set ALLOWED_PLUGIN_PREFIXES or ALLOW_ALL_PLUGINS=true for dev-only use.",
        )


class PluginRegistry:
    def __init__(self, policy: PluginPolicy | None = None) -> None:
        self._policy = policy or PluginPolicy.from_env()

    def load(self, path: str) -> Any:
        """Load an object from `module:Name` path with allowlist enforcement.

        - If Name is a class: instantiate with no args.
        - If Name is a function: call it with no args and use return value.
        - Otherwise: return the object itself.
        """
        if ":" not in path:
            raise ValueError("plugin path must be in form 'module:Name'")
        module_path, name = path.split(":", 1)
        module_path = module_path.strip()
        name = name.strip()
        if not module_path or not name:
            raise ValueError("plugin path must not be empty")

        self._policy.ensure_path_allowed(path)

        module = importlib.import_module(module_path)
        target = getattr(module, name, None)
        if target is None:
            raise ImportError(f"plugin target not found: {path}")

        if callable(target):
            try:
                return target()  # type: ignore[misc]
            except TypeError:
                # Not a no-arg callable; treat as object.
                return target
        return target

    @staticmethod
    def require_callable(obj: Any, attr: str) -> Callable[..., Any]:
        fn = getattr(obj, attr, None)
        if not callable(fn):
            raise TypeError(f"loaded plugin does not provide callable '{attr}()'")
        return fn
