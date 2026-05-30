"""Coverage for debug, parser, renderer, and CLI branches."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from template_engine.cli import main
from template_engine.context import ContextStack
from template_engine.debug import _format_expression, dump_ast
from template_engine.errors import RenderError
from template_engine.expressions import ConditionExpression, VariableExpression
from template_engine.lexer import lex
from template_engine.parser import parse
from template_engine.renderer import Renderer
from template_engine.template import Template


class RemainingCoverageTests(unittest.TestCase):
    def test_dump_raw_node(self):
        dump = dump_ast(Template("{% raw %}{{ x }}{% endraw %}").ast())
        self.assertIn("RawNode", dump)

    def test_format_expression_unknown(self):
        class Unknown:
            pass

        self.assertIn("Unknown", _format_expression(Unknown()))

    def test_format_expression_not_equals_condition(self):
        condition = ConditionExpression(
            "not_equals",
            VariableExpression(("a",)),
            VariableExpression(("b",)),
        )
        self.assertIn("!=", _format_expression(condition))

    def test_parser_stop_tag_at_root(self):
        from template_engine.errors import ParseError

        with self.assertRaises(ParseError):
            parse(list(lex("{% endif %}")))

    def test_parser_malformed_set(self):
        from template_engine.errors import ParseError

        with self.assertRaises(ParseError):
            parse(list(lex("{% set = 1 %}")))

    def test_renderer_bytes_iterable_rejected(self):
        renderer = Renderer(strict=True)
        stack = ContextStack({})
        from template_engine.nodes import ForNode

        node = ForNode("x", VariableExpression(("items",)), [], 1, 1)
        stack.scopes[-1]["items"] = b"abc"
        with self.assertRaises(RenderError):
            renderer._render_for(node, stack)

    def test_renderer_not_truthy_condition(self):
        renderer = Renderer()
        stack = ContextStack({"flag": False})
        condition = ConditionExpression("not_truthy", VariableExpression(("flag",)))
        self.assertTrue(renderer._evaluate_condition(condition, stack, line=1, column=1))

    def test_cli_verbose_token_dump(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                with redirect_stdout(io.StringIO()):
                    code = main(["-", "--dump-tokens", "-v"])
        self.assertEqual(code, 0)
        self.assertIn("tokens=", err.getvalue())

    def test_cli_check_success_verbose(self):
        err = io.StringIO()
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                with redirect_stdout(out):
                    code = main(["-", "--check", "-v"])
        self.assertEqual(code, 0)
        self.assertIn("nodes=", err.getvalue())


if __name__ == "__main__":
    unittest.main()
