"""Filter registry and built-in filters."""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterable
from typing import Any

from .context import MISSING
from .errors import RenderError
from .escape import SafeString, escape_html, mark_safe

# Re-export for callers that import SafeString from this module.
__all__ = [
    "FilterRegistry",
    "SafeString",
    "default_filter_registry",
]


class FilterRegistry:
    def __init__(self) -> None:
        self._filters: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, function: Callable[..., Any]) -> None:
        if not name.isidentifier() or name.startswith("_"):
            raise ValueError(f"invalid filter name {name!r}")
        self._filters[name] = function

    def get(self, name: str) -> Callable[..., Any]:
        try:
            return self._filters[name]
        except KeyError as exc:
            raise RenderError(f"unknown filter {name!r}") from exc

    def apply(self, name: str, value: Any, *args: Any) -> Any:
        function = self.get(name)
        try:
            return function(value, *args)
        except RenderError:
            raise
        except Exception as exc:  # noqa: BLE001 - convert expected filter failures for users.
            raise RenderError(f"filter {name!r} failed: {exc}") from exc

    def extend(self, other: FilterRegistry) -> None:
        """Register all filters from another registry, overwriting on name clash."""

        for name, function in other.all_filters().items():
            self.register(name, function)

    def all_filters(self) -> dict[str, Callable[..., Any]]:
        return dict(self._filters)


def default_filter_registry() -> FilterRegistry:
    registry = FilterRegistry()
    registry.register("upper", _upper)
    registry.register("lower", _lower)
    registry.register("title", _title)
    registry.register("trim", _trim)
    registry.register("default", _default)
    registry.register("default_if_none", _default_if_none)
    registry.register("length", _length)
    registry.register("join", _join)
    registry.register("round", _round)
    registry.register("escape", _escape)
    registry.register("safe", _safe)
    return registry


def _string(value: Any) -> str:
    if value is MISSING:
        return ""
    return str(value)


def _upper(value: Any) -> str:
    return _string(value).upper()


def _lower(value: Any) -> str:
    return _string(value).lower()


def _title(value: Any) -> str:
    return _string(value).title()


def _trim(value: Any) -> str:
    return _string(value).strip()


def _default(value: Any, fallback: Any = "") -> Any:
    if value is MISSING or value is None or value == "":
        return fallback
    return value


def _default_if_none(value: Any, fallback: Any = "") -> Any:
    if value is MISSING or value is None:
        return fallback
    return value


def _length(value: Any) -> int:
    if value is MISSING or value is None:
        return 0
    return len(value)


def _join(value: Any, separator: Any = "") -> str:
    if value is MISSING or value is None:
        return ""
    if isinstance(value, str):
        raise RenderError("join filter expected an iterable, not a string")
    if not isinstance(value, Iterable):
        raise RenderError("join filter expected an iterable")
    return str(separator).join(str(item) for item in value)


def _round(value: Any, ndigits: Any = 0) -> Any:
    if value is MISSING or value is None:
        return ""
    return builtins.round(float(value), int(ndigits))


def _escape(value: Any) -> SafeString:
    return escape_html(value)


def _safe(value: Any) -> SafeString:
    return mark_safe(value)
