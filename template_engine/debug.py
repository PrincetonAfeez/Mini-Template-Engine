"""Human-readable debug dumps for tokens and AST nodes."""

from __future__ import annotations

from typing import Any

from .expressions import ConditionExpression, FilterExpression, LiteralExpression, VariableExpression
from .nodes import ForNode, IfNode, RawNode, TemplateNode, TextNode, VariableNode
from .tokens import Token


def dump_tokens(tokens: list[Token]) -> str:
    lines = []
    for token in tokens:
        flags = []
        if token.trim_left:
            flags.append("trim_left")
        if token.trim_right:
            flags.append("trim_right")
        flag_text = f" {' '.join(flags)}" if flags else ""
        lines.append(
            f"{token.type.value} line={token.line} col={token.column}{flag_text} value={token.value!r}"
        )
    return "\n".join(lines)


def dump_ast(node: Any) -> str:
    lines: list[str] = []
    _dump_node(node, lines, 0)
    return "\n".join(lines)


def _dump_node(node: Any, lines: list[str], indent: int) -> None:
    prefix = "  " * indent
    if isinstance(node, TemplateNode):
        lines.append(f"{prefix}TemplateNode")
        for child in node.children:
            _dump_node(child, lines, indent + 1)
        return
    if isinstance(node, TextNode):
        lines.append(f"{prefix}TextNode({node.text!r})")
        return
    if isinstance(node, RawNode):
        lines.append(f"{prefix}RawNode({node.text!r})")
        return
    if isinstance(node, VariableNode):
        lines.append(f"{prefix}VariableNode({_format_expression(node.expression)})")
        return
    if isinstance(node, IfNode):
        lines.append(f"{prefix}IfNode")
        for branch in node.branches:
            lines.append(f"{prefix}  Branch({_format_expression(branch.condition)})")
            for child in branch.body:
                _dump_node(child, lines, indent + 2)
        if node.else_body:
            lines.append(f"{prefix}  Else")
            for child in node.else_body:
                _dump_node(child, lines, indent + 2)
        return
    if isinstance(node, ForNode):
        lines.append(
            f"{prefix}ForNode({node.item_name} in {_format_expression(node.iterable_expression)})"
        )
        for child in node.body:
            _dump_node(child, lines, indent + 1)
        return
    lines.append(f"{prefix}{type(node).__name__}")


def _format_expression(expression: Any) -> str:
    if isinstance(expression, VariableExpression):
        return ".".join(expression.path)
    if isinstance(expression, LiteralExpression):
        return repr(expression.value)
    if isinstance(expression, FilterExpression):
        filters = " | ".join(
            f"{call.name}({', '.join(repr(arg) for arg in call.args)})"
            if call.args
            else call.name
            for call in expression.filters
        )
        return f"{_format_expression(expression.base)} | {filters}"
    if isinstance(expression, ConditionExpression):
        if expression.kind == "truthy":
            return _format_expression(expression.left)
        if expression.kind == "not_truthy":
            return f"not {_format_expression(expression.left)}"
        operator = "==" if expression.kind == "equals" else "!="
        return f"{_format_expression(expression.left)} {operator} {_format_expression(expression.right)}"
    return repr(expression)
