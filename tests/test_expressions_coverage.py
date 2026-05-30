"""Full coverage for expressions.py helpers and branches."""

import unittest

from template_engine.errors import ParseError
from template_engine.expressions import (
    LiteralExpression,
    VariableExpression,
    _find_top_level_operator,
    _split_top_level,
    parse_condition_expression,
    parse_literal,
    parse_variable_expression,
)


class ExpressionsCoverageTests(unittest.TestCase):
    def test_not_prefix_without_operand(self):
        with self.assertRaises(ParseError):
            parse_condition_expression("not")

    def test_not_prefix_whitespace_only_operand(self):
        with self.assertRaises(ParseError):
            parse_condition_expression("not   ")

    def test_not_prefix_with_target(self):
        condition = parse_condition_expression("not disabled")
        self.assertEqual(condition.kind, "not_truthy")

    def test_invalid_string_literal_from_ast(self):
        with self.assertRaises(ParseError):
            parse_literal('"bad\\')

    def test_non_string_literal_eval_result(self):
        with self.assertRaises(ParseError):
            parse_literal("b'bytes'")

    def test_split_top_level_escape_and_paren_reset(self):
        parts = _split_top_level(r'"a\"b", x)', ",")
        self.assertEqual(parts[0], r'"a\"b"')
        parts = _split_top_level("a))", ",")
        self.assertEqual(parts, ["a))"])

    def test_split_top_level_unclosed_quote(self):
        with self.assertRaises(ParseError):
            _split_top_level('"open', ",")

    def test_find_operator_inside_quotes_and_parens(self):
        self.assertIsNone(_find_top_level_operator('"a==b"', ("==",)))
        self.assertIsNone(_find_top_level_operator("(a==b)", ("==",)))
        match = _find_top_level_operator("a == b", ("==",))
        self.assertIsNotNone(match)
        self.assertEqual(match[1], "==")

    def test_find_operator_with_nested_quotes(self):
        index, op = _find_top_level_operator('name == "x==y"', ("==",))
        self.assertEqual(op, "==")
        self.assertEqual(index, 5)

    def test_filter_with_escaped_argument(self):
        expression = parse_variable_expression(r'name|default("a,b")')
        self.assertIsInstance(expression.filters[0].args[0], LiteralExpression)
        self.assertEqual(expression.filters[0].args[0].value, "a,b")

    def test_condition_expression_types(self):
        condition = parse_condition_expression("flag")
        self.assertIsInstance(condition.left, VariableExpression)


if __name__ == "__main__":
    unittest.main()
