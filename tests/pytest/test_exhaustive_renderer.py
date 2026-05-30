"""Exhaustive pytest tests for template_engine.renderer."""

from __future__ import annotations

import pytest

from template_engine.context import MISSING, ContextStack
from template_engine.errors import RenderError
from template_engine.escape import SafeString
from template_engine.expressions import (
    ConditionExpression,
    FilterCall,
    FilterExpression,
    LiteralExpression,
    VariableExpression,
)
from template_engine.filters import FilterRegistry
from template_engine.nodes import ForNode, TemplateNode, TextNode
from template_engine.renderer import Renderer
from template_engine.template import Template


class TestRendererBasics:
    def test_render_text(self):
        renderer = Renderer()
        stack = ContextStack({})
        node = TextNode("hello", 1, 1)
        assert renderer._render_node(node, stack) == "hello"

    def test_render_template_node(self):
        renderer = Renderer()
        stack = ContextStack({})
        inner = TemplateNode([TextNode("x", 1, 1)])
        assert renderer._render_node(inner, stack) == "x"

    def test_autoescape(self):
        out = Template("{{ x }}").render({"x": "<b>"})
        assert out == "&lt;b&gt;"

    def test_no_autoescape(self):
        tmpl = Template("{{ x }}", autoescape=False)
        assert tmpl.render({"x": "<b>"}) == "<b>"

    def test_safe_string_not_double_escaped(self):
        out = Template("{{ x }}").render({"x": SafeString("<b>")})
        assert out == "<b>"

    def test_none_and_missing_stringify(self):
        renderer = Renderer()
        assert renderer._stringify(None) == ""
        assert renderer._stringify(MISSING) == ""


class TestRendererConditions:
    @pytest.fixture
    def renderer(self):
        return Renderer()

    @pytest.mark.parametrize(
        ("kind", "context", "expected"),
        [
            ("truthy", {"flag": True}, True),
            ("truthy", {"flag": False}, False),
            ("not_truthy", {"flag": False}, True),
            ("equals", {"a": 1, "b": 1}, True),
            ("not_equals", {"a": 1, "b": 2}, True),
        ],
    )
    def test_conditions(self, renderer, kind, context, expected):
        stack = ContextStack(context)
        if kind in {"truthy", "not_truthy"}:
            left = VariableExpression(("flag",)) if "flag" in context else VariableExpression(("a",))
            condition = ConditionExpression(kind, left)
        elif kind == "equals":
            condition = ConditionExpression(
                "equals", VariableExpression(("a",)), VariableExpression(("b",))
            )
        else:
            condition = ConditionExpression(
                "not_equals", VariableExpression(("a",)), VariableExpression(("b",))
            )
        assert renderer._evaluate_condition(condition, stack, line=1, column=1) is expected

    def test_equals_missing_right(self, renderer):
        stack = ContextStack({})
        condition = ConditionExpression("equals", VariableExpression(("x",)), None)
        with pytest.raises(RenderError, match="missing right side"):
            renderer._evaluate_condition(condition, stack, line=1, column=1)

    def test_not_equals_missing_right(self, renderer):
        stack = ContextStack({})
        condition = ConditionExpression("not_equals", VariableExpression(("x",)), None)
        with pytest.raises(RenderError, match="missing right side"):
            renderer._evaluate_condition(condition, stack, line=1, column=1)

    def test_unknown_condition_kind(self, renderer):
        stack = ContextStack({})
        condition = ConditionExpression("weird", VariableExpression(("x",)))
        with pytest.raises(RenderError, match="unknown condition kind"):
            renderer._evaluate_condition(condition, stack, line=1, column=1)


class TestRendererForLoop:
    def test_for_loop_with_loop_helper(self):
        out = Template("{% for x in items %}{{ loop.index }}{% endfor %}").render(
            {"items": ["a", "b"]}
        )
        assert out == "12"

    def test_for_missing_iterable_non_strict(self):
        out = Template("{% for x in items %}x{% endfor %}").render({})
        assert out == ""

    def test_for_none_iterable_non_strict(self):
        out = Template("{% for x in items %}x{% endfor %}").render({"items": None})
        assert out == ""

    def test_for_missing_strict(self):
        tmpl = Template("{% for x in items %}x{% endfor %}", strict=True)
        with pytest.raises(RenderError):
            tmpl.render({})

    def test_for_string_rejected_strict(self):
        tmpl = Template("{% for x in items %}x{% endfor %}", strict=True)
        with pytest.raises(RenderError, match="not a string"):
            tmpl.render({"items": "abc"})

    def test_for_bytes_rejected_strict(self):
        renderer = Renderer(strict=True)
        stack = ContextStack({"items": b"abc"})
        node = ForNode("x", VariableExpression(("items",)), [], 1, 1)
        with pytest.raises(RenderError):
            renderer._render_for(node, stack)

    def test_for_non_iterable_strict(self):
        tmpl = Template("{% for x in items %}x{% endfor %}", strict=True)
        with pytest.raises(RenderError, match="expected an iterable"):
            tmpl.render({"items": 42})


class TestRendererIfElse:
    def test_if_else_branch(self):
        out = Template("{% if no %}yes{% else %}no{% endif %}").render({"no": False})
        assert out == "no"


class TestRendererExpressions:
    def test_literal_expression(self):
        renderer = Renderer()
        stack = ContextStack({})
        assert renderer._evaluate(LiteralExpression(42), stack, line=1, column=1) == 42

    def test_filter_chain(self):
        out = Template("{{ name | upper | trim }}").render({"name": " ada "})
        assert out == "ADA"

    def test_strict_default_lenient_base(self):
        tmpl = Template("{{ missing | default('fb') }}", strict=True)
        assert tmpl.render({}) == "fb"

    def test_filter_error_gets_line_column(self):
        registry = FilterRegistry()
        registry.register("bad", lambda _v: (_ for _ in ()).throw(RenderError("fail")))
        renderer = Renderer(filters=registry)
        stack = ContextStack({})
        expr = FilterExpression(
            base=VariableExpression(("x",)),
            filters=[FilterCall("bad", [])],
        )
        with pytest.raises(RenderError) as exc:
            renderer._evaluate(expr, stack, line=5, column=3)
        assert exc.value.line == 5
        assert exc.value.column == 3

    def test_filter_error_preserves_existing_location(self):
        registry = FilterRegistry()
        registry.register("bad", lambda _v: (_ for _ in ()).throw(RenderError("fail", line=9, column=9)))
        renderer = Renderer(filters=registry)
        stack = ContextStack({})
        expr = FilterExpression(base=LiteralExpression("x"), filters=[FilterCall("bad", [])])
        with pytest.raises(RenderError) as exc:
            renderer._evaluate(expr, stack, line=5, column=3)
        assert exc.value.line == 9

    def test_none_expression(self):
        renderer = Renderer()
        stack = ContextStack({})
        assert renderer._evaluate(None, stack, line=1, column=1) is None  # type: ignore[arg-type]

    def test_unknown_expression_type(self):
        renderer = Renderer()
        stack = ContextStack({})
        with pytest.raises(RenderError, match="unknown expression"):
            renderer._evaluate(object(), stack, line=1, column=1)  # type: ignore[arg-type]

    def test_unknown_ast_node(self):
        renderer = Renderer()
        stack = ContextStack({})

        class FakeNode:
            pass

        with pytest.raises(RenderError, match="unknown AST node"):
            renderer._render_node(FakeNode(), stack)  # type: ignore[arg-type]


class TestRendererSet:
    def test_set_tag(self):
        out = Template("{% set greeting = 'hi' %}{{ greeting }}").render({})
        assert out == "hi"
