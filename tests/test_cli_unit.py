"""Direct unit tests for CLI and debug modules (coverage)."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from template_engine.cli import _load_filter_registry, main
from template_engine.debug import dump_ast, dump_tokens
from template_engine.template import Template


class CliUnitTests(unittest.TestCase):
    def test_main_version(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--version"])
        self.assertEqual(code, 0)
        self.assertRegex(buffer.getvalue().strip(), r"^\d+\.\d+\.\d+")

    def test_main_check_invalid_template(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{% if %}"):
            with redirect_stderr(err):
                code = main(["-", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("ParseError", err.getvalue())
        self.assertIn(">", err.getvalue())

    def test_main_dump_tokens(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--dump-tokens", "--include-comments"])
        self.assertEqual(code, 0)
        self.assertIn("VARIABLE", out.getvalue())

    def test_main_dump_ast(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--dump-ast"])
        self.assertEqual(code, 0)
        self.assertIn("TemplateNode", out.getvalue())

    def test_main_write_output_file(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            with patch("template_engine.cli._read_template", return_value="Hi {{ name }}"):
                code = main(["-", "--set", "name=You", "-o", str(output)])
            self.assertEqual(code, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "Hi You")

    def test_load_filter_registry_from_support_module(self):
        registry = _load_filter_registry("tests.support.custom_filters")
        self.assertEqual(registry.apply("exclaim", "x"), "x!")

    def test_load_filter_registry_bad_spec(self):
        with self.assertRaises(AttributeError):
            _load_filter_registry("tests.support.custom_filters:missing_attr")

    def test_verbose_render(self):
        err = io.StringIO()
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="Hi {{ name }}"):
            with redirect_stderr(err):
                with redirect_stdout(out):
                    code = main(["-", "--set", "name=You", "-v"])
        self.assertEqual(code, 0)
        self.assertIn("tokens=", err.getvalue())
        self.assertEqual(out.getvalue(), "Hi You")


class DebugUnitTests(unittest.TestCase):
    def test_dump_tokens_and_ast(self):
        template = Template("Hi {{ name }}")
        token_dump = dump_tokens(template.tokens())
        ast_dump = dump_ast(template.ast())
        self.assertIn("VARIABLE", token_dump)
        self.assertIn("VariableNode", ast_dump)
        self.assertIn("SetNode", dump_ast(Template("{% set x = 1 %}").ast()))


if __name__ == "__main__":
    unittest.main()
