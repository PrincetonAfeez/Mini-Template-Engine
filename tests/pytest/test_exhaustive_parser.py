"""Exhaustive pytest tests for template_engine.parser."""

from __future__ import annotations

import pytest

from template_engine.errors import ParseError
from template_engine.lexer import lex
from template_engine.nodes import ForNode, IfNode, RawNode, SetNode, TextNode, VariableNode
from template_engine.parser import Parser, _keyword, parse
from template_engine.tokens import TokenType


class TestKeyword:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("if x", "if"),
            ("  for item in items", "for"),
            ("endif", "endif"),
            ("", ""),
            ("   ", ""),
        ],
    )
    def test_keyword(self, value, expected):
        assert _keyword(value) == expected


class TestParse:
    def test_empty_template(self):
        ast = parse(lex(""))
        assert ast.children == []

    def test_text_and_variable(self):
        ast = parse(lex("Hello {{ name }}!"))
        assert len(ast.children) == 3
        assert isinstance(ast.children[0], TextNode)
        assert isinstance(ast.children[1], VariableNode)
        assert isinstance(ast.children[2], TextNode)

    def test_if_else_endif(self):
        ast = parse(lex("{% if x %}yes{% else %}no{% endif %}"))
        node = ast.children[0]
        assert isinstance(node, IfNode)
        assert len(node.branches) == 1
        assert node.else_body

    def test_if_elif_else(self):
        source = "{% if a %}1{% elif b %}2{% else %}3{% endif %}"
        node = parse(lex(source)).children[0]
        assert isinstance(node, IfNode)
        assert len(node.branches) == 2

    def test_for_loop(self):
        ast = parse(lex("{% for item in items %}{{ item }}{% endfor %}"))
        node = ast.children[0]
        assert isinstance(node, ForNode)
        assert node.item_name == "item"

    def test_set_tag(self):
        ast = parse(lex("{% set x = 1 %}"))
        assert isinstance(ast.children[0], SetNode)

    def test_raw_node_from_lexer(self):
        ast = parse(lex("{% raw %}{{ x }}{% endraw %}"))
        assert isinstance(ast.children[0], RawNode)

    def test_comments_skipped(self):
        ast = parse(lex("{# comment #}{{ x }}"))
        assert len(ast.children) == 1

    @pytest.mark.parametrize(
        ("source", "match"),
        [
            ("{% endif %}", "unexpected"),
            ("{% if x %}", "unclosed"),
            ("{% for x in y %}", "unclosed"),
            ("{% for _x in y %}{% endfor %}", "loop variable"),
            ("{% set _x = 1 %}", "set variable"),
            ("{% set = 1 %}", "malformed set"),
            ("{% for bad %}{% endfor %}", "malformed for"),
            ("{% else %}", "unexpected"),
            ("{% elif x %}", "unexpected"),
            ("{% if x %}{% else %}x{% end %}", "unknown block"),
            ("{% if x %}{% else arg %}{% endif %}", "does not take arguments"),
            ("{% if x %}{% endif arg %}", "does not take arguments"),
            ("{% for x in y %}{% endfor arg %}", "does not take arguments"),
        ],
    )
    def test_parse_errors(self, source, match):
        with pytest.raises(ParseError, match=match):
            parse(lex(source))

    def test_stop_tag_at_root(self):
        with pytest.raises(ParseError):
            parse(list(lex("{% endif %}")))

    def test_parser_current_past_end(self):
        parser = Parser(list(lex("x")))
        parser.parse()
        token = parser._current()
        assert token.type == TokenType.EOF

    def test_parser_eof_after_complete_parse(self):
        parser = Parser(list(lex("x")))
        parser.parse()
        parser._advance()
        token = parser._current()
        assert token.type == TokenType.EOF
        assert token.line == parser.tokens[-1].line
