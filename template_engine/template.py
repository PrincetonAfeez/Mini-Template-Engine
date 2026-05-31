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
    """Compile and render a template source string."""

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
        self._token_cache: dict[bool, list[Token]] = {}
        self._ast: TemplateNode | None = None

    def tokens(self, *, include_comments: bool = False) -> list[Token]:
        """Return the token stream, optionally including comment tokens."""

        cached = self._token_cache.get(include_comments)
        if cached is None:
            cached = list(lex(self.source, include_comments=include_comments))
            self._token_cache[include_comments] = cached
        return list(cached)

    def ast(self) -> TemplateNode:
        """Parse and cache the template AST."""

        if self._ast is None:
            self._ast = parse(self.tokens())
        return self._ast

    def check(self) -> Template:
        """Parse the template and return self when syntax is valid."""

        self.ast()
        return self

    def render(self, context: dict[str, Any] | None = None) -> str:
        """Render the template with the supplied context mapping."""

        renderer = Renderer(
            strict=self.strict,
            autoescape=self.autoescape,
            filters=self.filters,
        )
        return renderer.render(self.ast(), context or {})
