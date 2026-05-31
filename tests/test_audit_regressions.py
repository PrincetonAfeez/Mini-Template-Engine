"""Regression tests for the 30-item audit fix list."""

import unittest

from template_engine import Template, format_error
from template_engine.errors import ParseError, RenderError
from template_engine.expressions import (
    LiteralExpression,
    VariableExpression,
    parse_variable_expression,
)
from template_engine.lexer import lex
from template_engine.template import Template as TemplateClass
from template_engine.tokens import TokenType


class AuditRegressionTests(unittest.TestCase):
    def test_01_keyword_literals_in_output(self):
        self.assertEqual(Template("{{ true }}").render({}), "True")

    def test_02_strict_default_filter(self):
        output = Template('{{ missing | default("N/A") }}', strict=True).render({})
        self.assertEqual(output, "N/A")

    def test_03_property_errors_are_render_errors(self):
        class Broken:
            @property
            def value(self):
                raise RuntimeError("boom")

        with self.assertRaises(RenderError):
            Template("{{ item.value }}").render({"item": Broken()})

    def test_04_endraw_is_case_sensitive(self):
        from template_engine.errors import LexerError

        with self.assertRaises(LexerError):
            list(lex("{% raw %}x{% ENDRAW %}"))

    def test_05_variable_condition_comparison(self):
        source = "{% if user.role == expected %}yes{% endif %}"
        output = Template(source).render({"user": {"role": "a"}, "expected": "a"})
        self.assertEqual(output, "yes")

    def test_06_numeric_index_access(self):
        self.assertEqual(Template("{{ items.0 }}").render({"items": ["x"]}), "x")

    def test_07_variable_filter_arguments(self):
        expr = parse_variable_expression("value | default(fallback)")
        self.assertIsInstance(expr.filters[0].args[0], VariableExpression)

    def test_08_raw_blocks_for_literal_markers(self):
        output = Template("{% raw %}{{ x }}{% endraw %}").render({"x": 1})
        self.assertEqual(output, "{{ x }}")

    def test_09_dict_loop_iterates_keys(self):
        output = Template("{% for k in d %}{{ k }}{% endfor %}").render({"d": {"a": 1}})
        self.assertEqual(output, "a")

    def test_10_for_loop_rejects_strings_lenient(self):
        output = Template("{% for c in s %}x{% endfor %}").render({"s": "abc"})
        self.assertEqual(output, "")

    def test_12_include_comments_on_template_tokens(self):
        template = TemplateClass("{# note #}")
        tokens = template.tokens(include_comments=True)
        self.assertEqual(tokens[0].type, TokenType.COMMENT)

    def test_13_set_block(self):
        output = Template('{% set x = "1" %}{{ x }}').render({})
        self.assertEqual(output, "1")

    def test_15_literal_parsing_consistency(self):
        self.assertIsInstance(parse_variable_expression("null"), LiteralExpression)

    def test_17_default_if_none_preserves_empty_string(self):
        output = Template('{{ value | default_if_none("N/A") }}').render({"value": ""})
        self.assertEqual(output, "")

    def test_18_join_rejects_strings(self):
        with self.assertRaises(RenderError):
            Template('{{ value | join(",") }}').render({"value": "abc"})

    def test_19_format_error_includes_source_line(self):
        error = ParseError("bad tag", line=2, column=3)
        formatted = format_error(error, "a\n{% if %}\nc")
        self.assertIn("> {% if %}", formatted)
        self.assertIn("^", formatted)

    def test_21_check_returns_self(self):
        template = Template("hi")
        self.assertIs(template.check(), template)

    def test_29_keyword_literal_regression_render(self):
        self.assertEqual(Template("{{ false }}").render({}), "False")


if __name__ == "__main__":
    unittest.main()
