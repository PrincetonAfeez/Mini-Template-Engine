""" Test the expression parser. """

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
        self.assertEqual(expression.filters[1].args, ["N/A"])

    def test_literals(self):
        self.assertEqual(parse_literal('"x"'), "x")
        self.assertEqual(parse_literal("3"), 3)
        self.assertEqual(parse_literal("2.5"), 2.5)
        self.assertIs(parse_literal("true"), True)
        self.assertIs(parse_literal("null"), None)

    def test_conditions(self):
        truthy = parse_condition_expression("user")
        negated = parse_condition_expression("not user.disabled")
        equals = parse_condition_expression('user.role == "admin"')

        self.assertEqual(truthy.kind, "truthy")
        self.assertEqual(negated.kind, "not_truthy")
        self.assertIsInstance(equals, ConditionExpression)
        self.assertEqual(equals.right, LiteralExpression("admin"))

    def test_rejects_unsupported_condition_syntax(self):
        with self.assertRaises(ParseError):
            parse_condition_expression("user and admin")


if __name__ == "__main__":
    unittest.main()
