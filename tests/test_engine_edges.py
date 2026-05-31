"""Tests for remaining engine edge cases."""

import unittest

from template_engine.context import ContextStack
from template_engine.errors import LexerError, format_error
from template_engine.expressions import parse_condition_expression
from template_engine.parser import parse
from template_engine.renderer import Renderer
from template_engine.template import Template
from template_engine.tokens import Token, TokenType


class EngineEdgeTests(unittest.TestCase):
    def test_format_error_line_beyond_source(self):
        error = LexerError("bad", line=99, column=1)
        self.assertEqual(format_error(error, "one line"), str(error))

    def test_format_error_column_only(self):
        error = LexerError("bad", line=1)
        formatted = format_error(error, "hello")
        self.assertIn("hello", formatted)

    def test_truthy_condition_with_literal(self):
        condition = parse_condition_expression("true")
        renderer = Renderer()
        stack = ContextStack({})
        self.assertTrue(renderer._evaluate_condition(condition, stack, line=1, column=1))

    def test_parser_skips_comment_tokens(self):
        tokens = [
            Token(TokenType.COMMENT, "note", 1, 1),
            Token(TokenType.TEXT, "x", 1, 1),
            Token(TokenType.EOF, "", 1, 2),
        ]
        ast = parse(tokens)
        self.assertEqual(len(ast.children), 1)

    def test_context_pop_root_raises(self):
        stack = ContextStack({})
        from template_engine.errors import RenderError

        with self.assertRaises(RenderError):
            stack.pop()

    def test_strict_loop_invalid_iterable(self):
        from template_engine.errors import RenderError

        with self.assertRaises(RenderError):
            Template("{% for x in n %}{% endfor %}", strict=True).render({"n": 5})


if __name__ == "__main__":
    unittest.main()
