"""Security-focused rendering tests."""

import unittest

from template_engine import Template


class SecurityTests(unittest.TestCase):
    def test_autoescape_on_nested_markup(self):
        output = Template("{{ outer }}").render({"outer": "<script>alert(1)</script>"})
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

    def test_filter_output_still_escapes_without_safe(self):
        output = Template("{{ value | upper }}").render({"value": "<b>x</b>"})
        self.assertEqual(output, "&lt;B&gt;X&lt;/B&gt;")

    def test_safe_filter_prevents_re_escape(self):
        output = Template("{{ a | safe }}{{ b }}").render({"a": "<i>a</i>", "b": "<i>b</i>"})
        self.assertIn("<i>a</i>", output)
        self.assertIn("&lt;i&gt;b&lt;/i&gt;", output)

    def test_escape_filter_marks_safe_for_output(self):
        output = Template("{{ value | escape }}").render({"value": "<b>x</b>"})
        self.assertEqual(output, "&lt;b&gt;x&lt;/b&gt;")


if __name__ == "__main__":
    unittest.main()
