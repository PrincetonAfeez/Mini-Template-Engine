"""Remaining CLI helper coverage."""

import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from template_engine.cli import _apply_assignment, _load_filter_registry, main


class CliHelperTests(unittest.TestCase):
    def test_apply_assignment_nested_and_invalid(self):
        context: dict = {}
        _apply_assignment(context, "user.name=Ada")
        self.assertEqual(context["user"]["name"], "Ada")

        with self.assertRaises(ValueError):
            _apply_assignment(context, "noequals")

        with self.assertRaises(ValueError):
            _apply_assignment(context, "=bad")

        context["flat"] = "x"
        with self.assertRaises(ValueError):
            _apply_assignment(context, "flat.nope=1")

    def test_filter_registry_wrong_type(self):
        import types

        module = types.ModuleType("fake_filters")
        module.filter_registry = object()
        with patch("template_engine.cli.importlib.import_module", return_value=module):
            with self.assertRaises(ValueError):
                _load_filter_registry("fake_filters")

    def test_internal_error_path(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", side_effect=RuntimeError("boom")):
            with redirect_stderr(err):
                code = main(["-"])
        self.assertEqual(code, 3)
        self.assertIn("internal error", err.getvalue())

    def test_render_error_path(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ missing }}"):
            with redirect_stderr(err):
                code = main(["-", "--strict"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
