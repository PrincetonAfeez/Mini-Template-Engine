""" Test the escape helpers. """

import unittest

from template_engine.context import MISSING
from template_engine.escape import SafeString, escape_html, mark_safe


class EscapeTests(unittest.TestCase):
    def test_escape_html_returns_safe_string(self):
        value = escape_html('<a href="x">Hi</a>')
        self.assertIsInstance(value, SafeString)
        self.assertEqual(value, '&lt;a href=&quot;x&quot;&gt;Hi&lt;/a&gt;')

    def test_mark_safe_returns_safe_string(self):
        value = mark_safe("<b>x</b>")
        self.assertIsInstance(value, SafeString)
        self.assertEqual(value, "<b>x</b>")

    def test_missing_becomes_empty_string(self):
        self.assertEqual(escape_html(MISSING), "")
        self.assertEqual(mark_safe(MISSING), "")


if __name__ == "__main__":
    unittest.main()
