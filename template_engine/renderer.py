"""Recursive AST renderer."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .context import MISSING, ContextStack, LoopHelper
from .errors import RenderError
from .escape import SafeString, escape_html
from .expressions import (
    ConditionExpression,
    Expression,
    FilterExpression,
    LiteralExpression,
    VariableExpression,
)
from .filters import FilterRegistry, default_filter_registry
from .nodes import ASTNode, ForNode, IfNode, RawNode, SetNode, TemplateNode, TextNode, VariableNode


class Renderer:
    def __init__(
        self,
        *,
        strict: bool = False,
        autoescape: bool = True,
        filters: FilterRegistry | None = None,
    ) -> None:
        self.strict = strict
        self.autoescape = autoescape
        self.filters = filters or default_filter_registry()

    def render(self, node: TemplateNode, context: dict[str, Any] | None = None) -> str:
        stack = ContextStack(context or {}, strict=self.strict)
        return self._render_children(node.children, stack)

    def _render_children(self, children: list[ASTNode], stack: ContextStack) -> str:
        return "".join(self._render_node(child, stack) for child in children)

    def _render_node(self, node: ASTNode | TemplateNode, stack: ContextStack) -> str:
        if isinstance(node, TextNode):
            return node.text
        if isinstance(node, RawNode):
            return node.text
        if isinstance(node, VariableNode):
            value = self._evaluate(node.expression, stack, line=node.line, column=node.column)
            return self._stringify(value)
        if isinstance(node, SetNode):
            value = self._evaluate(node.expression, stack, line=node.line, column=node.column)
            stack.assign(node.name, value, line=node.line, column=node.column)
            return ""
        if isinstance(node, IfNode):
            for branch in node.branches:
                if self._evaluate_condition(
                    branch.condition, stack, line=node.line, column=node.column
                ):
                    return self._render_children(branch.body, stack)
            return self._render_children(node.else_body, stack)
        if isinstance(node, ForNode):
            return self._render_for(node, stack)
        if isinstance(node, TemplateNode):
            return self._render_children(node.children, stack)
        raise RenderError(f"unknown AST node {type(node).__name__}")

    def _render_for(self, node: ForNode, stack: ContextStack) -> str:
        iterable = self._evaluate(
            node.iterable_expression, stack, line=node.line, column=node.column
        )
        if iterable is MISSING or iterable is None:
            return self._missing_loop_value(node)
        if isinstance(iterable, (str, bytes)):
            return self._missing_loop_value(
                node, reason="for loop expected an iterable, not a string"
            )
        if not isinstance(iterable, Iterable):
            return self._missing_loop_value(node, reason="for loop expected an iterable")

        items = list(iterable)
        chunks: list[str] = []
        length = len(items)
        for index0, item in enumerate(items):
            stack.push(
                {
                    node.item_name: item,
                    "loop": LoopHelper(
                        index=index0 + 1,
                        index0=index0,
                        first=index0 == 0,
                        last=index0 == length - 1,
                        length=length,
                    ),
                }
            )
            try:
                chunks.append(self._render_children(node.body, stack))
            finally:
                stack.pop()
        return "".join(chunks)

    def _missing_loop_value(self, node: ForNode, *, reason: str | None = None) -> str:
        if self.strict:
            raise RenderError(
                reason or "for loop iterable is missing", line=node.line, column=node.column
            )
        return ""

    def _evaluate_condition(
        self,
        condition: ConditionExpression,
        stack: ContextStack,
        *,
        line: int | None,
        column: int | None,
    ) -> bool:
        left = self._evaluate(condition.left, stack, line=line, column=column)
        if condition.kind == "truthy":
            return bool(left)
        if condition.kind == "not_truthy":
            return not bool(left)
        if condition.kind == "equals":
            if condition.right is None:
                raise RenderError("equals condition missing right side", line=line, column=column)
            right = self._evaluate(condition.right, stack, line=line, column=column)
            return bool(left == right)
        if condition.kind == "not_equals":
            if condition.right is None:
                raise RenderError(
                    "not_equals condition missing right side", line=line, column=column
                )
            right = self._evaluate(condition.right, stack, line=line, column=column)
            return bool(left != right)
        raise RenderError(f"unknown condition kind {condition.kind!r}", line=line, column=column)

    def _evaluate(
        self,
        expression: Expression,
        stack: ContextStack,
        *,
        line: int | None,
        column: int | None,
        lenient: bool = False,
    ) -> Any:
        if isinstance(expression, LiteralExpression):
            return expression.value
        if isinstance(expression, VariableExpression):
            return stack.resolve(expression.path, line=line, column=column, lenient=lenient)
        if isinstance(expression, FilterExpression):
            has_default = any(call.name == "default" for call in expression.filters)
            base_lenient = lenient or (self.strict and has_default)
            value = self._evaluate(
                expression.base,
                stack,
                line=line,
                column=column,
                lenient=base_lenient,
            )
            for call in expression.filters:
                args = [self._evaluate(arg, stack, line=line, column=column) for arg in call.args]
                try:
                    value = self.filters.apply(call.name, value, *args)
                except RenderError as exc:
                    if exc.line is None and exc.column is None:
                        raise RenderError(exc.message, line=line, column=column) from exc
                    raise
            return value
        if expression is None:
            return None
        raise RenderError(
            f"unknown expression {type(expression).__name__}", line=line, column=column
        )

    def _stringify(self, value: Any) -> str:
        if value is MISSING or value is None:
            return ""
        if isinstance(value, SafeString):
            return str(value)
        if self.autoescape:
            return str(escape_html(value))
        return str(value)
