"""Targeted pytest tests for remaining coverage gaps."""

from __future__ import annotations

import pytest

from template_engine.context import ContextStack
from template_engine.errors import ParseError, RenderError
from template_engine.expressions import _find_top_level_operator
from template_engine.lexer import lex
from template_engine.parser import parse
from template_engine.tokens import TokenType


class TestLexerRemainingGaps:
    def test_trim_previous_on_raw_token(self):
        source = "{% raw %}content   {% endraw %}{{- x }}"
        tokens = list(lex(source))
        raw = next(t for t in tokens if t.type == TokenType.RAW)
        assert raw.value == "content"

    def test_emit_text_empty_after_pending_trim(self):
        tokens = list(lex("{{ a -}}   {{ b }}"))
        text = [t for t in tokens if t.type == TokenType.TEXT]
        assert text == []


class TestParserRemainingGaps:
    def test_stop_tag_at_root_via_parse(self):
        with pytest.raises(ParseError, match="unexpected"):
            parse(list(lex("{% endif %}")))

    def test_endif_wrong_keyword(self):
        with pytest.raises(ParseError):
            parse(list(lex("{% if x %}y{% endfor %}")))

    def test_endif_with_extra_keyword(self):
        with pytest.raises(ParseError, match="does not take arguments"):
            parse(list(lex("{% if x %}y{% endif extra %}")))


class TestExpressionsRemainingGaps:
    def test_find_operator_escape_then_quote(self):
        result = _find_top_level_operator(r'name == "a\"b"', ("==",))
        assert result == (5, "==")

class TestContextRemainingGaps:
    def test_callable_after_nested_resolution(self):
        """Covers defensive callable check after multi-segment path resolution."""

        class Box:
            def __init__(self, value):
                self.value = value

        stack = ContextStack({"box": Box(lambda: 1)})
        with pytest.raises(RenderError, match="callable"):
            stack.resolve(("box", "value"))
