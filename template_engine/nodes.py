"""AST node dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TemplateNode:
    children: list[Any]


@dataclass(frozen=True)
class TextNode:
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class VariableNode:
    expression: Any
    line: int
    column: int


@dataclass(frozen=True)
class RawNode:
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class IfBranch:
    condition: Any
    body: list[Any]


@dataclass(frozen=True)
class IfNode:
    branches: list[IfBranch]
    else_body: list[Any]
    line: int
    column: int


@dataclass(frozen=True)
class ForNode:
    item_name: str
    iterable_expression: Any
    body: list[Any]
    line: int
    column: int
