"""Additional CLI paths for coverage."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from template_engine.cli import main


class CliCoverageTests(unittest.TestCase):
    def test_check_success(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ ok }}"):
            with redirect_stdout(out):
                code = main(["-", "--check"])
        self.assertEqual(code, 0)
        self.assertIn("ok", out.getvalue())

    def test_mutually_exclusive_modes(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="x"):
            with redirect_stderr(err):
                with self.assertRaises(SystemExit):
                    main(["-", "--check", "--dump-tokens"])
        # argparse exits via SystemExit on error

    def test_invalid_context_json(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            err = io.StringIO()
            with patch("template_engine.cli._read_template", return_value="x"):
                with redirect_stderr(err):
                    code = main(["-", "--context", str(bad)])
            self.assertEqual(code, 2)

    def test_context_not_object(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "list.json"
            bad.write_text(json.dumps([1, 2]), encoding="utf-8")
            err = io.StringIO()
            with patch("template_engine.cli._read_template", return_value="x"):
                with redirect_stderr(err):
                    code = main(["-", "--context", str(bad)])
            self.assertEqual(code, 2)

    def test_filter_module_not_found(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                code = main(["-", "--filter-module", "no_such_module_ever"])
        self.assertEqual(code, 2)

    def test_invalid_set_value(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                code = main(["-", "--set", "bad"])
        self.assertEqual(code, 2)

    def test_no_autoescape_render(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--set", "x=<b>", "--no-autoescape"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "<b>")


if __name__ == "__main__":
    unittest.main()
