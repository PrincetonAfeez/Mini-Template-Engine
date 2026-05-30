"""HTML escaping helpers."""

from __future__ import annotations

import html
from typing import Any

from .context import MISSING


class SafeString(str):
    """A string that should not be escaped again by the renderer."""


def escape_html(value: Any) -> SafeString:
    if value is MISSING:
        return SafeString("")
    if isinstance(value, SafeString):
        return value
    return SafeString(html.escape(str(value), quote=True))


def mark_safe(value: Any) -> SafeString:
    if value is MISSING:
        return SafeString("")
    if isinstance(value, SafeString):
        return value
    return SafeString(str(value))
