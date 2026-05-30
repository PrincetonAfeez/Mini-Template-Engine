"""Exhaustive pytest tests for template_engine.debug."""

from __future__ import annotations

from template_engine.debug import _format_expression, dump_ast, dump_tokens
from template_engine.expressions import (
    ConditionExpression,
    FilterCall,
    FilterExpression,
    LiteralExpression,
    VariableExpression,
)
from template_engine.template import Template
from template_engine.tokens import Token, TokenType


class TestDumpTokens:
    def test_dump_text_token(self):
        tokens = [Token(TokenType.TEXT, "hi", 1, 1)]
        output = dump_tokens(tokens)
        assert "TEXT" in output
        assert "value='hi'" in output

    def test_dump_trim_flags(self):
        tokens = [Token(TokenType.VARIABLE, "x", 1, 1, True, True)]
        output = dump_tokens(tokens)
        assert "trim_left" in output
        assert "trim_right" in output


class TestDumpAst:
    def test_dump_full_template(self):
        ast = Template("{% if x %}{{ x }}{% endif %}").ast()
        output = dump_ast(ast)
        assert "TemplateNode" in output
        assert "IfNode" in output
        assert "VariableNode" in output

    def test_dump_raw_node(self):
        output = dump_ast(Template("{% raw %}{{ x }}{% endraw %}").ast())
        assert "RawNode" in output

    def test_dump_for_and_set(self):
        source = "{% for i in items %}{% set x = 1 %}{% endfor %}"
        output = dump_ast(Template(source).ast())
        assert "ForNode" in output
        assert "SetNode" in output

    def test_dump_if_with_else(self):
        source = "{% if x %}a{% else %}b{% endif %}"
        output = dump_ast(Template(source).ast())
        assert "Else" in output


class TestFormatExpression:
    def test_variable(self):
        assert _format_expression(VariableExpression(("user", "name"))) == "user.name"

    def test_literal(self):
        assert _format_expression(LiteralExpression(42)) == "42"

    def test_filter_no_args(self):
        expr = FilterExpression(VariableExpression(("x",)), [FilterCall("upper", [])])
        assert _format_expression(expr) == "x | upper"

    def test_filter_with_args(self):
        expr = FilterExpression(
            VariableExpression(("x",)),
            [FilterCall("default", [LiteralExpression("fb")])],
        )
        assert "default('fb')" in _format_expression(expr)

    def test_condition_truthy(self):
        cond = ConditionExpression("truthy", VariableExpression(("x",)))
        assert _format_expression(cond) == "x"

    def test_condition_not_truthy(self):
        cond = ConditionExpression("not_truthy", VariableExpression(("x",)))
        assert _format_expression(cond) == "not x"

    def test_condition_equals(self):
        cond = ConditionExpression(
            "equals",
            VariableExpression(("a",)),
            VariableExpression(("b",)),
        )
        assert _format_expression(cond) == "a == b"

    def test_condition_not_equals(self):
        cond = ConditionExpression(
            "not_equals",
            VariableExpression(("a",)),
            VariableExpression(("b",)),
        )
        assert _format_expression(cond) == "a != b"

    def test_unknown_expression_type(self):
        class Unknown:
            pass

        output = _format_expression(Unknown())
        assert "Unknown" in output

    def test_unknown_ast_node_fallback(self):
        class FakeNode:
            pass

        lines: list[str] = []
        from template_engine.debug import _dump_node

        _dump_node(FakeNode(), lines, 0)
        assert lines == ["FakeNode"]
