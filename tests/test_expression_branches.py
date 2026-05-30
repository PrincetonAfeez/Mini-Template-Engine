"""Target expression parser branches for coverage."""

import unittest

from template_engine.errors import ParseError
from template_engine.expressions import (
    _parse_filter_call,
    parse_condition_expression,
    parse_literal,
    parse_variable_expression,
)


class ExpressionBranchTests(unittest.TestCase):
    def test_invalid_string_literals(self):
        with self.assertRaises(ParseError):
            parse_literal('"mismatch\'')
        with self.assertRaises(ParseError):
            parse_literal("''bad")

    def test_float_literals(self):
        self.assertEqual(parse_literal(".5"), 0.5)
        self.assertEqual(parse_literal("1e2"), 100.0)

    def test_filter_errors(self):
        with self.assertRaises(ParseError):
            _parse_filter_call("", line=1, column=1)
        with self.assertRaises(ParseError):
            _parse_filter_call("_hidden", line=1, column=1)
        with self.assertRaises(ParseError):
            _parse_filter_call("bad syntax!", line=1, column=1)
        with self.assertRaises(ParseError):
            parse_variable_expression('name | default("x",)')

    def test_bare_not_is_parse_error(self):
        with self.assertRaises(ParseError):
            parse_condition_expression("not")

    def test_condition_not_equal(self):
        condition = parse_condition_expression("left != right")
        self.assertEqual(condition.kind, "not_equals")

    def test_filter_with_escaped_commas(self):
        expression = parse_variable_expression('name | default("a,b")')
        self.assertEqual(expression.filters[0].args[0].value, "a,b")


if __name__ == "__main__":
    unittest.main()
