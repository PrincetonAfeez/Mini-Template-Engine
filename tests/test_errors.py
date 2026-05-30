""" Test the error classes. """

import unittest

from template_engine.errors import LexerError, ParseError, RenderError, TemplateEngineError


class ErrorTests(unittest.TestCase):
    def test_errors_include_stage_name_and_location(self):
        error = ParseError("bad tag", line=2, column=4)
        self.assertEqual(str(error), "ParseError at line 2, column 4: bad tag")

    def test_errors_share_base_class(self):
        self.assertIsInstance(LexerError("x"), TemplateEngineError)
        self.assertIsInstance(ParseError("x"), TemplateEngineError)
        self.assertIsInstance(RenderError("x"), TemplateEngineError)


if __name__ == "__main__":
    unittest.main()
