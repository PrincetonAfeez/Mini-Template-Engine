"""Exhaustive pytest tests for template_engine.lexer."""

from __future__ import annotations

import pytest

from template_engine.errors import LexerError
from template_engine.lexer import _find_next_opener, _line_starts, _read_tag, lex
from template_engine.tokens import TokenType


class TestLineStarts:
    def test_single_line(self):
        assert _line_starts("hello") == [0]

    def test_multiline(self):
        assert _line_starts("a\nb\nc") == [0, 2, 4]


class TestFindNextOpener:
    def test_no_opener(self):
        assert _find_next_opener("plain text", 0) == (-1, "")

    def test_earliest_wins(self):
        index, opener = _find_next_opener("a {{ x }} {% y %}", 0)
        assert opener == "{{"
        assert index == 2


class TestReadTag:
    def test_variable_tag(self):
        token, end = _read_tag("{{ name }}", 0, "}}", TokenType.VARIABLE, 1, 1)
        assert token.value == "name"
        assert end == len("{{ name }}")

    def test_trim_markers(self):
        token, _ = _read_tag("{{- name -}}", 0, "}}", TokenType.VARIABLE, 1, 1)
        assert token.trim_left is True
        assert token.trim_right is True

    def test_unterminated(self):
        with pytest.raises(LexerError, match="unterminated"):
            _read_tag("{{ name", 0, "}}", TokenType.VARIABLE, 1, 1)


class TestLex:
    def test_plain_text(self):
        tokens = list(lex("hello world"))
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "hello world"
        assert tokens[-1].type == TokenType.EOF

    def test_variable_token(self):
        tokens = list(lex("{{ x }}"))
        assert tokens[0].type == TokenType.VARIABLE
        assert tokens[0].value == "x"

    def test_block_token(self):
        tokens = list(lex("{% if x %}{% endif %}"))
        blocks = [t for t in tokens if t.type == TokenType.BLOCK]
        assert len(blocks) == 2

    def test_comments_excluded_by_default(self):
        tokens = list(lex("{# note #}"))
        assert all(t.type != TokenType.COMMENT for t in tokens)

    def test_comments_included(self):
        tokens = list(lex("{# note #}", include_comments=True))
        assert tokens[0].type == TokenType.COMMENT

    def test_raw_block(self):
        tokens = list(lex("{% raw %}{{ x }}{% endraw %}"))
        assert tokens[0].type == TokenType.RAW
        assert tokens[0].value == "{{ x }}"

    def test_raw_case_insensitive_endraw(self):
        tokens = list(lex("{% raw %}x{% ENDRAW %}"))
        assert tokens[0].value == "x"

    def test_unterminated_raw(self):
        with pytest.raises(LexerError, match="unterminated raw"):
            list(lex("{% raw %}never ends"))

    def test_unterminated_variable(self):
        with pytest.raises(LexerError):
            list(lex("{{ broken"))

    def test_whitespace_trim_left(self):
        tokens = list(lex("hello   {{- x -}}   world"))
        text_values = [t.value for t in tokens if t.type == TokenType.TEXT]
        assert "hello" in text_values[0]
        assert text_values[-1].startswith("world")

    def test_whitespace_trim_right_on_raw(self):
        source = "before{% raw -%}  {{ x }}  {%- endraw %}after"
        tokens = list(lex(source))
        raw = next(t for t in tokens if t.type == TokenType.RAW)
        assert "{{ x }}" in raw.value

    def test_trim_pops_empty_text(self):
        tokens = list(lex("   {{- x }}"))
        text_tokens = [t for t in tokens if t.type == TokenType.TEXT]
        assert text_tokens == []

    def test_comment_trim_previous(self):
        tokens = list(lex("hello   {#- note #}world", include_comments=True))
        text = [t for t in tokens if t.type == TokenType.TEXT]
        assert text[0].value == "hello"

    def test_pending_trim_right_empty_emit(self):
        tokens = list(lex("{{- x -}}"))
        assert all(t.type != TokenType.TEXT for t in tokens[:-1])
