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

    def test_safe_survives_string_transform_filters(self):
        # `safe` marks the value as already-trusted HTML; chaining `upper`
        # must not strip that marking and trigger another autoescape pass.
        output = Template("{{ value | safe | upper }}").render({"value": "<b>x</b>"})
        self.assertEqual(output, "<B>X</B>")

    def test_escape_survives_string_transform_filters(self):
        # `escape` returns SafeString containing already-escaped HTML;
        # chaining `upper` must not re-encode the entities.
        output = Template("{{ value | escape | upper }}").render({"value": "<b>x</b>"})
        self.assertEqual(output, "&LT;B&GT;X&LT;/B&GT;")

    def test_descriptor_access_is_rejected(self):
        from template_engine.errors import RenderError

        class _Descriptor:
            def __get__(self, obj, owner):
                return "computed-value"

        class _Obj:
            attr = _Descriptor()

        with self.assertRaises(RenderError):
            Template("{{ x.attr }}").render({"x": _Obj()})


if __name__ == "__main__":
    unittest.main()
