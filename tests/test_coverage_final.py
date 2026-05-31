"""Final coverage helpers for context, renderer, and CLI."""

import unittest
from unittest.mock import patch

from template_engine.context import MISSING, ContextStack
from template_engine.errors import RenderError
from template_engine.expressions import ConditionExpression, VariableExpression
from template_engine.renderer import Renderer


class FinalCoverageTests(unittest.TestCase):
    def test_missing_value_dunder_methods(self):
        self.assertFalse(MISSING)
        self.assertEqual(str(MISSING), "")
        self.assertEqual(repr(MISSING), "MISSING")

    def test_renderer_missing_condition_sides(self):
        renderer = Renderer()
        stack = ContextStack({})
        equals = ConditionExpression("equals", VariableExpression(("x",)), None)
        not_equals = ConditionExpression("not_equals", VariableExpression(("x",)), None)
        with self.assertRaises(RenderError):
            renderer._evaluate_condition(equals, stack, line=1, column=1)
        with self.assertRaises(RenderError):
            renderer._evaluate_condition(not_equals, stack, line=1, column=1)

    def test_renderer_unknown_expression_type(self):
        renderer = Renderer()
        stack = ContextStack({})
        with self.assertRaises(RenderError):
            renderer._evaluate(object(), stack, line=1, column=1)  # type: ignore[arg-type]

    def test_cli_verbose_dump_ast(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout

        from template_engine.cli import main

        err = io.StringIO()
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                with redirect_stdout(out):
                    code = main(["-", "--dump-ast", "-v"])
        self.assertEqual(code, 0)
        self.assertIn("top_level_nodes=", err.getvalue())


if __name__ == "__main__":
    unittest.main()
