"""Parser and lexer edge-case tests."""

from __future__ import annotations

import pytest

from template_engine import Template
from template_engine.errors import ParseError


def test_empty_template_parses_and_renders_empty():
    assert Template("").render({}) == ""


def test_large_template_renders():
    source = "Hello {{ name }}\n" * 10_000
    output = Template(source).render({"name": "Princeton"})
    assert output.count("Hello Princeton") == 10_000


def test_unclosed_string_literal_in_variable_raises():
    with pytest.raises(ParseError):
        Template('{{ name | default("missing) }}').check()


def test_malformed_escape_in_variable_expression_raises():
    with pytest.raises(ParseError):
        Template(r'{{ name | default("bad\") }}').check()


def test_oversized_single_line_text_renders():
    source = "x" * 100_000 + "{{ ok }}"
    assert Template(source).render({"ok": "!"}) == "x" * 100_000 + "!"
