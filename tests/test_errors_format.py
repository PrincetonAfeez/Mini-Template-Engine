"""Tests for error formatting helpers."""

import unittest

from template_engine.errors import LexerError, ParseError, RenderError, format_error


class ErrorFormatTests(unittest.TestCase):
    def test_format_without_source(self):
        error = RenderError("missing", line=1, column=4)
        self.assertEqual(format_error(error), str(error))

    def test_format_with_source_pointer(self):
        source = "Hello {{ name\n"
        error = LexerError("unterminated variable tag", line=1, column=7)
        formatted = format_error(error, source)
        self.assertIn("LexerError", formatted)
        self.assertIn("> Hello {{ name", formatted)
        self.assertIn("^", formatted)

    def test_format_line_only_location(self):
        error = ParseError("bad", line=3)
        self.assertIn("line 3", str(error))


if __name__ == "__main__":
    unittest.main()
