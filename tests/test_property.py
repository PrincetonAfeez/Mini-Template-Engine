"""Property-based tests for expression parsing."""

import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from template_engine.errors import ParseError
from template_engine.expressions import LiteralExpression, parse_variable_expression


class PropertyTests(unittest.TestCase):
    @given(st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=25)
    def test_integer_literals_round_trip(self, value: int):
        expression = parse_variable_expression(str(value))
        self.assertIsInstance(expression, LiteralExpression)
        self.assertEqual(expression.value, value)

    @given(st.sampled_from(["alpha", "beta_name", "user_1", "Data"]))
    @settings(max_examples=10)
    def test_simple_paths_parse(self, name: str):
        expression = parse_variable_expression(name)
        self.assertEqual(expression.path, (name,))

    @given(st.sampled_from(["true", "false", "none", "null"]))
    def test_keyword_literals_parse(self, keyword: str):
        expression = parse_variable_expression(keyword)
        self.assertIsInstance(expression, LiteralExpression)

    def test_unclosed_string_rejected(self):
        with self.assertRaises(ParseError):
            parse_variable_expression('x | default("open)')


if __name__ == "__main__":
    unittest.main()
