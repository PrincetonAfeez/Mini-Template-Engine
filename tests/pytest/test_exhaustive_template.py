"""Exhaustive pytest tests for template_engine.template facade."""

from __future__ import annotations

import pytest

from template_engine.errors import RenderError
from template_engine.filters import FilterRegistry
from template_engine.template import Template
from template_engine.tokens import TokenType


class TestTemplateFacade:
    def test_tokens_cached(self):
        tmpl = Template("{{ x }}")
        first = tmpl.tokens()
        second = tmpl.tokens()
        assert first == second
        assert first[0].type == TokenType.VARIABLE

    def test_tokens_include_comments_not_cached_same(self):
        tmpl = Template("{# note #}{{ x }}")
        with_comments = tmpl.tokens(include_comments=True)
        without = tmpl.tokens()
        assert any(t.type == TokenType.COMMENT for t in with_comments)
        assert all(t.type != TokenType.COMMENT for t in without)

    def test_ast_cached(self):
        tmpl = Template("{{ x }}")
        assert tmpl.ast() is tmpl.ast()

    def test_check_returns_self(self):
        tmpl = Template("ok")
        assert tmpl.check() is tmpl

    def test_render_with_context(self):
        assert Template("{{ a }}-{{ b }}").render({"a": 1, "b": 2}) == "1-2"

    def test_render_default_empty_context(self):
        assert Template("static").render() == "static"

    def test_custom_filters(self):
        registry = FilterRegistry()
        registry.register("double", lambda v: str(v) * 2)
        out = Template("{{ x | double }}", filters=registry).render({"x": "a"})
        assert out == "aa"

    def test_strict_flag_propagates(self):
        tmpl = Template("{{ missing }}", strict=True)
        with pytest.raises(RenderError):
            tmpl.render({})

    def test_autoescape_flag(self):
        tmpl = Template("{{ x }}", autoescape=False)
        assert tmpl.render({"x": "<b>"}) == "<b>"

    def test_source_preserved(self):
        source = "{% if x %}{{ x }}{% endif %}"
        assert Template(source).source == source
