"""Exhaustive pytest tests for template_engine.expressions."""

from __future__ import annotations

import pytest

from template_engine.errors import ParseError
from template_engine.expressions import (
    FilterCall,
    FilterExpression,
    LiteralExpression,
    VariableExpression,
    _find_top_level_operator,
    _is_path,
    _parse_filter_call,
    _split_top_level,
    parse_condition_expression,
    parse_literal,
    parse_value_expression,
    parse_variable_expression,
)


class TestParseLiteral:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("true", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("none", None),
            ("null", None),
            ("0", 0),
            ("+7", 7),
            ("-3", -3),
            ("1.5", 1.5),
            (".5", 0.5),
            ("1e2", 100.0),
            ("'hello'", "hello"),
            ('"world"', "world"),
            (r"'a\'b'", "a'b"),
        ],
    )
    def test_valid_literals(self, text, expected):
        assert parse_literal(text) == expected

    @pytest.mark.parametrize(
        "text",
        ["unquoted", "not_a_float..", '"mismatch\'', "''bad", "b'bytes'", '"bad\\'],
    )
    def test_invalid_literals(self, text):
        with pytest.raises(ParseError):
            parse_literal(text)

    def test_literal_eval_syntax_error(self):
        with pytest.raises(ParseError, match="invalid string literal"):
            parse_literal('"\\"')

    def test_literal_eval_non_string_result(self, monkeypatch):
        import template_engine.expressions as expr_module

        monkeypatch.setattr(expr_module.ast, "literal_eval", lambda _text: 42)
        with pytest.raises(ParseError, match="invalid string literal"):
            parse_literal('"x"')


class TestParseValueExpression:
    @pytest.mark.parametrize(
        ("text", "expected_type"),
        [
            ("42", LiteralExpression),
            ("name", VariableExpression),
            ("user.name", VariableExpression),
            ("items.0", VariableExpression),
        ],
    )
    def test_value_expressions(self, text, expected_type):
        expr = parse_value_expression(text)
        assert isinstance(expr, expected_type)

    def test_unsupported_expression(self):
        with pytest.raises(ParseError, match="unsupported"):
            parse_value_expression("!!!")


class TestParseVariableExpression:
    def test_simple_variable(self):
        expr = parse_variable_expression("name")
        assert isinstance(expr, VariableExpression)
        assert expr.path == ("name",)

    def test_filter_chain(self):
        expr = parse_variable_expression("name | upper | trim")
        assert isinstance(expr, FilterExpression)
        assert len(expr.filters) == 2
        assert expr.filters[0].name == "upper"
        assert expr.filters[1].name == "trim"

    def test_filter_with_args(self):
        expr = parse_variable_expression(r'name|default("a,b")')
        assert expr.filters[0].args[0].value == "a,b"

    @pytest.mark.parametrize(
        "text",
        ["", "| upper", "name |", "name | default(\"x\",)"],
    )
    def test_invalid_variable_expressions(self, text):
        with pytest.raises(ParseError):
            parse_variable_expression(text)


class TestParseConditionExpression:
    @pytest.mark.parametrize(
        ("text", "kind"),
        [
            ("flag", "truthy"),
            ("not disabled", "not_truthy"),
            ("a == b", "equals"),
            ("left != right", "not_equals"),
        ],
    )
    def test_condition_kinds(self, text, kind):
        condition = parse_condition_expression(text)
        assert condition.kind == kind

    @pytest.mark.parametrize("text", ["", "   ", "not"])
    def test_empty_or_bare_not(self, text):
        with pytest.raises(ParseError):
            parse_condition_expression(text)


class TestParseFilterCall:
    def test_no_args(self):
        call = _parse_filter_call("upper", line=1, column=1)
        assert call == FilterCall(name="upper", args=[])

    def test_with_args(self):
        call = _parse_filter_call('default("x")', line=1, column=1)
        assert call.name == "default"
        assert len(call.args) == 1

    @pytest.mark.parametrize(
        "text",
        ["", "_hidden", "bad syntax!", "9bad"],
    )
    def test_invalid_filter_calls(self, text):
        with pytest.raises(ParseError):
            _parse_filter_call(text, line=1, column=1)


class TestSplitTopLevel:
    def test_simple_split(self):
        assert _split_top_level("a,b,c", ",") == ["a", "b", "c"]

    def test_quoted_comma(self):
        parts = _split_top_level(r'"a,b", x', ",")
        assert parts == [r'"a,b"', " x"]

    def test_escaped_quote_inside_string(self):
        parts = _split_top_level(r'"a\"b", x', ",")
        assert parts[0] == r'"a\"b"'

    def test_paren_depth(self):
        parts = _split_top_level("a(b,c),d", ",")
        assert parts == ["a(b,c)", "d"]

    def test_unclosed_quote(self):
        with pytest.raises(ParseError, match="unclosed"):
            _split_top_level('"open', ",")


class TestFindTopLevelOperator:
    def test_finds_equals(self):
        match = _find_top_level_operator("a == b", ("==",))
        assert match == (2, "==")

    def test_ignores_inside_quotes(self):
        assert _find_top_level_operator('"a==b"', ("==",)) is None

    def test_ignores_inside_parens(self):
        assert _find_top_level_operator("(a==b)", ("==",)) is None

    def test_escape_sequence_in_quotes(self):
        index, op = _find_top_level_operator('name == "x\\"y"', ("==",))
        assert op == "=="
        assert index == 5


class TestIsPath:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("name", True),
            ("user.name", True),
            ("items.0", True),
            ("", False),
            ("bad-name", False),
            ("9start", False),
        ],
    )
    def test_is_path(self, text, expected):
        assert _is_path(text) is expected
