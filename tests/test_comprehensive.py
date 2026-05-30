"""Broad tests to cover remaining engine branches."""

import unittest

from template_engine.context import MISSING, ContextStack
from template_engine.errors import ParseError, RenderError
from template_engine.escape import SafeString, escape_html, mark_safe
from template_engine.expressions import (
    parse_condition_expression,
    parse_literal,
    parse_value_expression,
    parse_variable_expression,
)
from template_engine.filters import FilterRegistry, default_filter_registry
from template_engine.lexer import lex
from template_engine.parser import parse
from template_engine.renderer import Renderer
from template_engine.template import Template


class ComprehensiveEngineTests(unittest.TestCase):
    def test_escape_safe_string_paths(self):
        safe = SafeString("<b>")
        self.assertIs(escape_html(safe), safe)
        self.assertIs(mark_safe(safe), safe)
        self.assertEqual(str(mark_safe(MISSING)), "")

    def test_filter_registry_validation_and_errors(self):
        registry = FilterRegistry()
        with self.assertRaises(ValueError):
            registry.register("9bad", lambda v: v)
        with self.assertRaises(ValueError):
            registry.register("_hidden", lambda v: v)
        with self.assertRaises(RenderError):
            registry.apply("missing", "x")

        def boom(_value):
            raise RuntimeError("fail")

        registry.register("boom", boom)
        with self.assertRaises(RenderError):
            registry.apply("boom", "x")

    def test_all_builtin_filter_edges(self):
        registry = default_filter_registry()
        self.assertEqual(registry.apply("default_if_none", MISSING, "x"), "x")
        self.assertEqual(registry.apply("length", None), 0)
        self.assertEqual(registry.apply("round", None), "")
        with self.assertRaises(RenderError):
            registry.apply("join", 123)

    def test_expression_parse_errors(self):
        with self.assertRaises(ParseError):
            parse_variable_expression("")
        with self.assertRaises(ParseError):
            parse_value_expression("!!!")
        with self.assertRaises(ParseError):
            parse_condition_expression("")
        with self.assertRaises(ParseError):
            parse_condition_expression("   ")
        with self.assertRaises(ParseError):
            parse_literal("unquoted")
        with self.assertRaises(ParseError):
            parse_variable_expression("| upper")

    def test_expression_string_and_numeric_literals(self):
        self.assertEqual(parse_literal("'a\\'b'"), "a'b")
        self.assertEqual(parse_literal("1.0"), 1.0)
        self.assertEqual(parse_literal("+7"), 7)

    def test_context_callable_and_private_paths(self):
        stack = ContextStack({"fn": lambda: 1})
        with self.assertRaises(RenderError):
            stack.resolve(("fn",))
        stack = ContextStack({"user": {"name": "x"}})
        with self.assertRaises(RenderError):
            stack.resolve(("user", "_secret"))
        obj = type("Obj", (), {"_x": 1})()
        stack = ContextStack({"obj": obj})
        with self.assertRaises(RenderError):
            stack.resolve(("obj", "_x"))

    def test_context_callable_nested(self):
        stack = ContextStack({"items": [{"run": lambda: None}]})
        with self.assertRaises(RenderError):
            stack.resolve(("items", "0", "run"))

    def test_lexer_comment_include_and_raw_trim(self):
        tokens = list(lex("{%- raw -%} x {%- endraw -%}", include_comments=True))
        self.assertTrue(any(token.type.value == "COMMENT" for token in tokens) is False)
        list(lex("{% raw %}{% endraw %}"))

    def test_parser_error_paths(self):
        with self.assertRaises(ParseError):
            parse(list(lex("{% unknown %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% else %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% if x %}{% else extra %}{% endif %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% if x %}{% endif extra %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% for x %}{% endfor %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% for x in y %}{% endfor extra %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% set bad %}")))
        with self.assertRaises(ParseError):
            parse(list(lex("{% set _x = 1 %}")))

    def test_renderer_unknown_condition_and_expression(self):
        renderer = Renderer()
        stack = ContextStack({})
        bad_condition = parse_condition_expression("true")
        object.__setattr__(bad_condition, "kind", "weird")
        with self.assertRaises(RenderError):
            renderer._evaluate_condition(bad_condition, stack, line=1, column=1)

    def test_renderer_strict_missing_loop(self):
        with self.assertRaises(RenderError):
            Template("{% for x in missing %}{% endfor %}", strict=True).render({})

    def test_renderer_template_node_branch(self):
        renderer = Renderer()
        stack = ContextStack({})
        node = Template("hi").ast()
        self.assertEqual(renderer._render_node(node, stack), "hi")

    def test_filter_registry_extend(self):
        source = default_filter_registry()
        target = FilterRegistry()
        target.extend(source)
        self.assertEqual(target.apply("upper", "a"), "A")

    def test_condition_with_quoted_operator(self):
        condition = parse_condition_expression('name == "a==b"')
        self.assertEqual(condition.kind, "equals")

    def test_cli_stdin_read_path(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch

        from template_engine.cli import main

        out = StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ 'ok' }}"):
            with redirect_stdout(out):
                self.assertEqual(main(["-"]), 0)


if __name__ == "__main__":
    unittest.main()
