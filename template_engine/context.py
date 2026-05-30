"""Context stack and variable resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .errors import RenderError


class MissingValue:
    """Sentinel used for lenient missing variable resolution."""

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "MISSING"


MISSING = MissingValue()


@dataclass(frozen=True)
class LoopHelper:
    index: int
    index0: int
    first: bool
    last: bool
    length: int


class ContextStack:
    def __init__(self, initial: Mapping[str, Any] | None = None, *, strict: bool = False) -> None:
        self.scopes: list[Mapping[str, Any]] = [dict(initial or {})]
        self.strict = strict

    def push(self, scope: Mapping[str, Any]) -> None:
        self.scopes.append(scope)

    def pop(self) -> None:
        if len(self.scopes) == 1:
            raise RenderError("cannot pop root context scope")
        self.scopes.pop()

    def resolve(
        self,
        path: tuple[str, ...],
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> Any:
        if not path:
            return self._missing("<empty>", line=line, column=column)

        value = self._resolve_first(path[0], line=line, column=column)
        for part in path[1:]:
            if value is MISSING:
                return MISSING
            value = self._resolve_part(value, part, full_path=".".join(path), line=line, column=column)
        if callable(value):
            raise RenderError(
                f"variable {'.'.join(path)!r} resolved to a callable",
                line=line,
                column=column,
            )
        return value

    def _resolve_first(self, name: str, *, line: int | None, column: int | None) -> Any:
        self._reject_private(name, line=line, column=column)
        for scope in reversed(self.scopes):
            if name in scope:
                value = scope[name]
                if callable(value):
                    raise RenderError(f"variable {name!r} resolved to a callable", line=line, column=column)
                return value
        return self._missing(name, line=line, column=column)

    def _resolve_part(
        self,
        value: Any,
        part: str,
        *,
        full_path: str,
        line: int | None,
        column: int | None,
    ) -> Any:
        self._reject_private(part, line=line, column=column)
        if isinstance(value, Mapping):
            if part in value:
                result = value[part]
                if callable(result):
                    raise RenderError(f"variable {full_path!r} resolved to a callable", line=line, column=column)
                return result
            return self._missing(full_path, line=line, column=column)

        if hasattr(value, part):
            result = getattr(value, part)
            if callable(result):
                raise RenderError(f"variable {full_path!r} resolved to a callable", line=line, column=column)
            return result

        return self._missing(full_path, line=line, column=column)

    def _reject_private(self, name: str, *, line: int | None, column: int | None) -> None:
        if name.startswith("_"):
            raise RenderError(f"private attribute access is not allowed: {name!r}", line=line, column=column)

    def _missing(self, name: str, *, line: int | None, column: int | None) -> Any:
        if self.strict:
            raise RenderError(f"missing variable {name!r}", line=line, column=column)
        return MISSING
