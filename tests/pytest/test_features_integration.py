"""Integration pytest tests covering every template language feature."""

from __future__ import annotations

from pathlib import Path

import pytest

from template_engine import Template
from template_engine.errors import LexerError, ParseError, RenderError


@pytest.mark.integration
class TestExampleTemplates:
    @pytest.fixture
    def examples(self, examples_dir: Path) -> Path:
        return examples_dir

    @pytest.fixture
    def context(self, invoice_context: dict) -> dict:
        return invoice_context

    @pytest.mark.parametrize(
        "name",
        ["hello.tmpl", "loop.tmpl", "conditions.tmpl", "invoice.tmpl", "showcase.tmpl"],
    )
    def test_example_renders(self, examples: Path, context: dict, name: str):
        source = (examples / name).read_text(encoding="utf-8")
        output = Template(source).render(context)
        assert isinstance(output, str)
        assert len(output) > 0


@pytest.mark.integration
class TestLanguageFeatures:
    @pytest.mark.parametrize(
        ("source", "context", "expected"),
        [
            ("{{ name }}", {"name": "Ada"}, "Ada"),
            ("{{ name | upper }}", {"name": "ada"}, "ADA"),
            ("{{ name | default('anon') }}", {}, "anon"),
            ("{{ name | default_if_none('anon') }}", {"name": ""}, ""),
            ("{{ items | length }}", {"items": [1, 2]}, "2"),
            ("{{ items | join(', ') }}", {"items": ["a", "b"]}, "a, b"),
            ("{{ pi | round(2) }}", {"pi": 3.14159}, "3.14"),
            ("{{ html | escape }}", {"html": "<b>"}, "&lt;b&gt;"),
            ("{{ html | safe }}", {"html": "<b>"}, "<b>"),
            ("{% if show %}yes{% endif %}", {"show": True}, "yes"),
            ("{% if show %}yes{% else %}no{% endif %}", {"show": False}, "no"),
            ("{% if a %}1{% elif b %}2{% else %}3{% endif %}", {"a": False, "b": True}, "2"),
            ("{% for x in items %}{{ x }}{% endfor %}", {"items": ["a", "b"]}, "ab"),
            (
                "{% for x in items %}{{ loop.index }}:{{ loop.first }}:{{ loop.last }};{% endfor %}",
                {"items": ["a", "b"]},
                "1:True:False;2:False:True;",
            ),
            ("{% set x = 'hi' %}{{ x }}", {}, "hi"),
            ("{% raw %}{{ not parsed }}{% endraw %}", {}, "{{ not parsed }}"),
            ("{# comment #}visible", {}, "visible"),
            ("before{{- x -}}after", {"x": "M"}, "beforeMafter"),
            ("{{ true }}", {}, "True"),
            ("{{ none }}", {}, ""),
            ("{{ items.0 }}", {"items": ["first"]}, "first"),
            ("{{ user.name }}", {"user": {"name": "Ada"}}, "Ada"),
            ("{% if name == 'Ada' %}ok{% endif %}", {"name": "Ada"}, "ok"),
            ("{% if name != 'Bob' %}ok{% endif %}", {"name": "Ada"}, "ok"),
            ("{% if not hidden %}ok{% endif %}", {"hidden": False}, "ok"),
        ],
    )
    def test_feature(self, source, context, expected):
        assert Template(source).render(context) == expected

    def test_autoescape_by_default(self):
        assert Template("{{ x }}").render({"x": "<script>"}) == "&lt;script&gt;"

    def test_strict_missing_variable(self):
        with pytest.raises(RenderError):
            Template("{{ missing }}", strict=True).render({})

    def test_strict_with_default_filter(self):
        assert Template("{{ x | default('fb') }}", strict=True).render({}) == "fb"


@pytest.mark.integration
class TestErrorPaths:
    @pytest.mark.parametrize(
        "source",
        [
            "{{ unclosed",
            "{% if x %}",
            "{% for x in y %}",
            "{% raw %}",
        ],
    )
    def test_lexer_or_parse_errors(self, source):
        with pytest.raises((LexerError, ParseError)):
            Template(source).check()

    def test_join_filter_on_string(self):
        with pytest.raises(RenderError):
            Template("{{ x | join }}").render({"x": "abc"})
