"""AST node dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .expressions import ConditionExpression, Expression


@dataclass(frozen=True)
class TemplateNode:
    """Root node containing top-level template children."""

    children: tuple[ASTNode, ...]


@dataclass(frozen=True)
class TextNode:
    """Literal text output."""

    text: str
    line: int
    column: int


@dataclass(frozen=True)
class VariableNode:
    """Variable or expression output tag."""

    expression: Expression
    line: int
    column: int


@dataclass(frozen=True)
class RawNode:
    """Literal text from a raw block."""

    text: str
    line: int
    column: int


@dataclass(frozen=True)
class IfBranch:
    """One branch of an if/elif chain."""

    condition: ConditionExpression
    body: tuple[ASTNode, ...]


@dataclass(frozen=True)
class IfNode:
    """Conditional block."""

    branches: tuple[IfBranch, ...]
    else_body: tuple[ASTNode, ...]
    line: int
    column: int


@dataclass(frozen=True)
class ForNode:
    """For loop block."""

    item_name: str
    iterable_expression: Expression
    body: tuple[ASTNode, ...]
    line: int
    column: int


@dataclass(frozen=True)
class SetNode:
    """Assignment block that binds a name in the current scope."""

    name: str
    expression: Expression
    line: int
    column: int


ASTNode = TextNode | VariableNode | RawNode | IfNode | ForNode | SetNode
