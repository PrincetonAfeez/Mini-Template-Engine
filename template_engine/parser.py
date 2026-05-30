"""Parser that turns tokens into an AST."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .errors import ParseError
from .expressions import parse_condition_expression, parse_variable_expression
from .nodes import ForNode, IfBranch, IfNode, RawNode, TemplateNode, TextNode, VariableNode
from .tokens import Token, TokenType

_FOR_RE = re.compile(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)$", flags=re.DOTALL)


def parse(tokens: Iterable[Token]) -> TemplateNode:
    return Parser(list(tokens)).parse()


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> TemplateNode:
        children, stop = self._parse_nodes(stop_tags=set())
        if stop is not None:
            raise self._unexpected_block(stop)
        return TemplateNode(children)

    def _parse_nodes(self, *, stop_tags: set[str]) -> tuple[list[object], Token | None]:
        children: list[object] = []
        while True:
            token = self._current()
            if token.type == TokenType.EOF:
                return children, None
            if token.type == TokenType.TEXT:
                self._advance()
                children.append(TextNode(token.value, token.line, token.column))
                continue
            if token.type == TokenType.RAW:
                self._advance()
                children.append(RawNode(token.value, token.line, token.column))
                continue
            if token.type == TokenType.COMMENT:
                self._advance()
                continue
            if token.type == TokenType.VARIABLE:
                self._advance()
                expression = parse_variable_expression(
                    token.value,
                    line=token.line,
                    column=token.column,
                )
                children.append(VariableNode(expression, token.line, token.column))
                continue
            if token.type == TokenType.BLOCK:
                keyword = _keyword(token.value)
                if keyword in stop_tags:
                    return children, token
                if keyword == "if":
                    children.append(self._parse_if())
                    continue
                if keyword == "for":
                    children.append(self._parse_for())
                    continue
                raise self._unexpected_block(token)

            raise ParseError(f"unexpected token {token.type.value}", line=token.line, column=token.column)

    def _parse_if(self) -> IfNode:
        first = self._advance()
        condition_text = first.value[len("if") :].strip()
        condition = parse_condition_expression(
            condition_text,
            line=first.line,
            column=first.column,
        )

        branches: list[IfBranch] = []
        body, stop = self._parse_nodes(stop_tags={"elif", "else", "endif"})
        branches.append(IfBranch(condition, body))
        else_body: list[object] = []

        while stop is not None and _keyword(stop.value) == "elif":
            elif_token = self._advance()
            elif_text = elif_token.value[len("elif") :].strip()
            elif_condition = parse_condition_expression(
                elif_text,
                line=elif_token.line,
                column=elif_token.column,
            )
            body, stop = self._parse_nodes(stop_tags={"elif", "else", "endif"})
            branches.append(IfBranch(elif_condition, body))

        if stop is not None and _keyword(stop.value) == "else":
            else_token = self._advance()
            if else_token.value.strip() != "else":
                raise ParseError("{% else %} does not take arguments", line=else_token.line, column=else_token.column)
            else_body, stop = self._parse_nodes(stop_tags={"endif"})

        if stop is None:
            raise ParseError(
                f"unclosed {{% if %}} opened at line {first.line}",
                line=first.line,
                column=first.column,
            )

        endif = self._advance()
        if _keyword(endif.value) != "endif":
            raise self._unexpected_block(endif)
        if endif.value.strip() != "endif":
            raise ParseError("{% endif %} does not take arguments", line=endif.line, column=endif.column)

        return IfNode(branches, else_body, first.line, first.column)

    def _parse_for(self) -> ForNode:
        first = self._advance()
        match = _FOR_RE.fullmatch(first.value.strip())
        if not match:
            raise ParseError(
                "malformed for tag; expected {% for item in items %}",
                line=first.line,
                column=first.column,
            )

        item_name, iterable_text = match.groups()
        if item_name.startswith("_"):
            raise ParseError("loop variable cannot start with '_'", line=first.line, column=first.column)

        iterable_expression = parse_variable_expression(
            iterable_text,
            line=first.line,
            column=first.column,
        )
        body, stop = self._parse_nodes(stop_tags={"endfor"})
        if stop is None:
            raise ParseError(
                f"unclosed {{% for %}} opened at line {first.line}",
                line=first.line,
                column=first.column,
            )

        endfor = self._advance()
        if endfor.value.strip() != "endfor":
            raise ParseError("{% endfor %} does not take arguments", line=endfor.line, column=endfor.column)

        return ForNode(item_name, iterable_expression, body, first.line, first.column)

    def _current(self) -> Token:
        if self.position >= len(self.tokens):
            last = self.tokens[-1]
            return Token(TokenType.EOF, "", last.line, last.column)
        return self.tokens[self.position]

    def _advance(self) -> Token:
        token = self._current()
        self.position += 1
        return token

    def _unexpected_block(self, token: Token) -> ParseError:
        keyword = _keyword(token.value)
        if keyword in {"elif", "else", "endif", "endfor", "endraw"}:
            return ParseError(f"unexpected {{% {keyword} %}}", line=token.line, column=token.column)
        return ParseError(f"unknown block tag {keyword!r}", line=token.line, column=token.column)


def _keyword(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return stripped.split(maxsplit=1)[0]
