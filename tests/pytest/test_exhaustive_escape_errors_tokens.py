"""Exhaustive pytest tests for escape, errors, tokens, and MissingValue."""

from __future__ import annotations

import pytest

from template_engine.context import MISSING, MissingValue
from template_engine.errors import LexerError, ParseError, RenderError, TemplateEngineError, format_error
from template_engine.escape import SafeString, escape_html, mark_safe
from template_engine.tokens import Token, TokenType


class TestMissingValue:
    def test_bool(self):
        assert not MISSING
        assert bool(MissingValue()) is False

    def test_str_repr(self):
        assert str(MISSING) == ""
        assert repr(MISSING) == "MISSING"


class TestEscape:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("<script>", "&lt;script&gt;"),
            ("a & b", "a &amp; b"),
            ('"quote"', "&quot;quote&quot;"),
            ("", ""),
            (42, "42"),
        ],
    )
    def test_escape_html(self, raw, expected):
        result = escape_html(raw)
        assert isinstance(result, SafeString)
        assert result == expected

    def test_escape_html_missing(self):
        assert escape_html(MISSING) == ""

    def test_escape_html_none(self):
        assert escape_html(None) == ""

    def test_mark_safe_none(self):
        assert mark_safe(None) == ""

    def test_escape_html_safe_passthrough(self):
        safe = SafeString("<b>ok</b>")
        assert escape_html(safe) is safe

    def test_mark_safe(self):
        assert mark_safe("<b>") == "<b>"
        assert isinstance(mark_safe("<b>"), SafeString)

    def test_mark_safe_missing_and_safe(self):
        assert mark_safe(MISSING) == ""
        safe = SafeString("x")
        assert mark_safe(safe) is safe


class TestErrors:
    def test_error_str_line_only(self):
        err = LexerError("oops", line=3)
        assert "line 3" in str(err)
        assert "column" not in str(err)

    def test_error_str_line_and_column(self):
        err = ParseError("bad", line=1, column=4)
        assert "line 1, column 4" in str(err)

    def test_error_message_attribute(self):
        err = RenderError("fail")
        assert err.message == "fail"

    def test_format_error_with_pointer(self):
        source = "line1\nbad {{ x\nline3"
        err = ParseError("unexpected", line=2, column=6)
        formatted = format_error(err, source)
        assert "unexpected" in formatted
        assert "> bad {{ x" in formatted
        assert "^" in formatted

    def test_format_error_line_beyond_source(self):
        err = ParseError("x", line=99, column=1)
        assert format_error(err, "one line") == str(err)

    def test_format_error_no_line(self):
        err = TemplateEngineError("generic")
        assert format_error(err, "source") == str(err)


class TestTokens:
    def test_token_fields(self):
        token = Token(TokenType.TEXT, "hi", 1, 1, True, False)
        assert token.type == TokenType.TEXT
        assert token.value == "hi"
        assert token.trim_left is True
        assert token.trim_right is False

    @pytest.mark.parametrize("member", list(TokenType))
    def test_token_type_members(self, member: TokenType):
        assert isinstance(member.value, str)
