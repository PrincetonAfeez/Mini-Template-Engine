""" Test the renderer. """

import unittest

from template_engine.errors import RenderError
from template_engine.template import Template


class RendererTests(unittest.TestCase):
    def test_variable_renders_and_autoescapes(self):
        output = Template("Hello {{ name }}").render({"name": "<Admin>"})
        self.assertEqual(output, "Hello &lt;Admin&gt;")

    def test_safe_filter_prevents_escaping(self):
        output = Template("{{ value | safe }}").render({"value": "<b>x</b>"})
        self.assertEqual(output, "<b>x</b>")

    def test_no_autoescape(self):
        output = Template("{{ value }}", autoescape=False).render({"value": "<b>x</b>"})
        self.assertEqual(output, "<b>x</b>")

    def test_filters_and_default(self):
        output = Template('{{ missing | default("N/A") | upper }}').render({})
        self.assertEqual(output, "N/A")

    def test_if_elif_else(self):
        source = "{% if user.admin %}A{% elif user.staff %}S{% else %}U{% endif %}"
        output = Template(source).render({"user": {"admin": False, "staff": True}})
        self.assertEqual(output, "S")

    def test_for_loop_and_loop_helpers(self):
        source = "{% for user in users %}{{ loop.index0 }}:{{ loop.index }}:{{ loop.length }}:{{ loop.first }}:{{ loop.last }}={{ user.name }};{% endfor %}"
        output = Template(source).render({"users": [{"name": "A"}, {"name": "B"}]})
        self.assertEqual(output, "0:1:2:True:False=A;1:2:2:False:True=B;")

    def test_loop_scope_does_not_clobber_outer_context(self):
        source = "{{ item }}{% for item in items %}{{ item }}{% endfor %}{{ item }}"
        output = Template(source).render({"item": "outer", "items": ["a", "b"]})
        self.assertEqual(output, "outerabouter")

    def test_raw_and_comments(self):
        output = Template("A{# hidden #}{% raw %}{{ name }}{% endraw %}").render({"name": "x"})
        self.assertEqual(output, "A{{ name }}")

    def test_strict_missing_raises(self):
        with self.assertRaises(RenderError):
            Template("{{ missing }}", strict=True).render({})

    def test_non_iterable_loop_lenient_renders_nothing(self):
        output = Template("A{% for x in value %}{{ x }}{% endfor %}B").render({"value": "abc"})
        self.assertEqual(output, "AB")


if __name__ == "__main__":
    unittest.main()
