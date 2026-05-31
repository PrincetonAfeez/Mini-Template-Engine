"""Test the command-line interface."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cli(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, "-m", "template_engine", *args],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_render_file_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "hello.tmpl"
            context = Path(tmp) / "context.json"
            template.write_text("Hello {{ name }}", encoding="utf-8")
            context.write_text(json.dumps({"name": "Princeton"}), encoding="utf-8")

            result = self.run_cli(str(template), "--context", str(context))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "Hello Princeton")

    def test_render_stdin_and_inline_set(self):
        result = self.run_cli("-", "--set", "name=Princeton", input_text="Hello {{ name }}")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Hello Princeton")

    def test_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            result = self.run_cli("-", "--set", "name=Princeton", "-o", str(output), input_text="Hi {{ name }}")

            self.assertEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "Hi Princeton")

    def test_check_dump_tokens_and_dump_ast(self):
        check = self.run_cli("-", "--check", input_text="{% if user %}x{% endif %}")
        tokens = self.run_cli("-", "--dump-tokens", input_text="Hi {{ name }}")
        ast = self.run_cli("-", "--dump-ast", input_text="Hi {{ name }}")

        self.assertEqual(check.returncode, 0)
        self.assertIn("ok", check.stdout)
        self.assertIn("VARIABLE", tokens.stdout)
        self.assertIn("VariableNode", ast.stdout)

    def test_invalid_template_exits_one(self):
        result = self.run_cli("-", "--check", input_text="{% if user %}")

        self.assertEqual(result.returncode, 1)
        self.assertIn("ParseError", result.stderr)

    def test_missing_file_exits_two(self):
        result = self.run_cli("does-not-exist.tmpl")

        self.assertEqual(result.returncode, 2)

    def test_version_flag(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout.strip(), r"^\d+\.\d+\.\d+")

    def test_verbose_renders_to_stderr(self):
        result = self.run_cli("-", "--set", "name=Test", "-v", input_text="Hi {{ name }}")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tokens=", result.stderr)

    def test_include_comments_dump(self):
        result = self.run_cli("-", "--dump-tokens", "--include-comments", input_text="{# note #}x")
        self.assertEqual(result.returncode, 0)
        self.assertIn("COMMENT", result.stdout)

    def test_strict_loop_error(self):
        result = self.run_cli("-", "--strict", input_text="{% for x in value %}{{ x }}{% endfor %}")
        self.assertEqual(result.returncode, 1)
        self.assertIn("RenderError", result.stderr)

    def test_parse_error_shows_source_excerpt(self):
        result = self.run_cli("-", "--check", input_text="Hello {{ name")
        self.assertEqual(result.returncode, 1)
        self.assertIn(">", result.stderr)

    def test_filter_module_loads_custom_filter(self):
        result = self.run_cli(
            "-",
            "--filter-module",
            "tests.support.custom_filters",
            "--set",
            "name=Hi",
            input_text="{{ name | exclaim }}",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, "Hi!")

    def test_filter_module_import_error_exits_two(self):
        result = self.run_cli("-", "--filter-module", "definitely_missing_module", input_text="x")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
