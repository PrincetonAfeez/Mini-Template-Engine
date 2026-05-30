""" Test the command-line interface. """

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


if __name__ == "__main__":
    unittest.main()
