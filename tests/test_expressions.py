"""Test the expression parser."""

import unittest

from template_engine.errors import ParseError
from template_engine.expressions import (
    ConditionExpression,
    FilterExpression,
    LiteralExpression,
    VariableExpression,
    parse_condition_expression,
    parse_literal,
    parse_variable_expression,
)


class ExpressionTests(unittest.TestCase):
    def test_dotted_variable(self):
        expression = parse_variable_expression("user.profile.email")
        self.assertEqual(expression, VariableExpression(("user", "profile", "email")))

    def test_filter_chain_with_arguments(self):
        expression = parse_variable_expression('name | trim | default("N/A")')
        self.assertIsInstance(expression, FilterExpression)
        self.assertEqual(expression.filters[0].name, "trim")
        self.assertEqual(expression.filters[1].args, [LiteralExpression("N/A")])

    def test_literals(self):
        self.assertEqual(parse_literal('"x"'), "x")
        self.assertEqual(parse_literal("3"), 3)
        self.assertEqual(parse_literal("2.5"), 2.5)
        self.assertIs(parse_literal("true"), True)
        self.assertIs(parse_literal("null"), None)

    def test_keyword_literals_in_output_position(self):
        expression = parse_variable_expression("true")
        self.assertEqual(expression, LiteralExpression(True))

    def test_numeric_path_segments(self):
        expression = parse_variable_expression("items.0.name")
        self.assertEqual(expression, VariableExpression(("items", "0", "name")))

    def test_filter_arguments_may_be_variables(self):
        expression = parse_variable_expression("price | default(fallback)")
        self.assertIsInstance(expression, FilterExpression)
        self.assertEqual(expression.filters[0].args, [VariableExpression(("fallback",))])

    def test_conditions(self):
        truthy = parse_condition_expression("user")
        negated = parse_condition_expression("not user.disabled")
        equals = parse_condition_expression('user.role == "admin"')
        variable_compare = parse_condition_expression("user.role == expected")

        self.assertEqual(truthy.kind, "truthy")
        self.assertEqual(negated.kind, "not_truthy")
        self.assertIsInstance(equals, ConditionExpression)
        self.assertEqual(equals.right, LiteralExpression("admin"))
        self.assertEqual(variable_compare.right, VariableExpression(("expected",)))

    def test_rejects_unsupported_condition_syntax(self):
        with self.assertRaises(ParseError):
            parse_condition_expression("user and admin")

    def test_unclosed_string_in_filter_argument(self):
        with self.assertRaises(ParseError):
            parse_variable_expression('x | default("unclosed)')


if __name__ == "__main__":
    unittest.main()
