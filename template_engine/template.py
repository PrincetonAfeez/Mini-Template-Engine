"""Public Template facade."""

from __future__ import annotations

from typing import Any

from .filters import FilterRegistry
from .lexer import lex
from .nodes import TemplateNode
from .parser import parse
from .renderer import Renderer
from .tokens import Token


class Template:
    def __init__(
        self,
        source: str,
        *,
        strict: bool = False,
        autoescape: bool = True,
        filters: FilterRegistry | None = None,
    ) -> None:
        self.source = source
        self.strict = strict
        self.autoescape = autoescape
        self.filters = filters
        self._tokens: list[Token] | None = None
        self._ast: TemplateNode | None = None

    def tokens(self) -> list[Token]:
        if self._tokens is None:
            self._tokens = list(lex(self.source))
        return list(self._tokens)

    def ast(self) -> TemplateNode:
        if self._ast is None:
            self._ast = parse(self.tokens())
        return self._ast

    def check(self) -> None:
        self.ast()

    def render(self, context: dict[str, Any] | None = None) -> str:
        renderer = Renderer(
            strict=self.strict,
            autoescape=self.autoescape,
            filters=self.filters,
        )
        return renderer.render(self.ast(), context or {})
