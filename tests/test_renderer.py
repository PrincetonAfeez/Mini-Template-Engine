"""Test the renderer."""

import unittest

from template_engine.errors import RenderError
from template_engine.template import Template


class RendererTests(unittest.TestCase):
    def test_empty_template_renders_empty(self):
        self.assertEqual(Template("").render({}), "")

    def test_large_template_renders_without_crashing(self):
        source = "Hello {{ name }}\n" * 10_000
        output = Template(source).render({"name": "Princeton"})

        self.assertIn("Hello Princeton", output)
        self.assertEqual(output.count("Hello Princeton"), 10_000)

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

    def test_keyword_literals_render(self):
        output = Template("{{ true }}-{{ false }}-{{ none }}").render({})
        self.assertEqual(output, "True-False-")

    def test_strict_default_filter_still_works(self):
        output = Template('{{ missing | default("N/A") }}', strict=True).render({})
        self.assertEqual(output, "N/A")

    def test_set_block_renders(self):
        output = Template('{% set label = "Hi" %}{{ label }} {{ name }}').render({"name": "there"})
        self.assertEqual(output, "Hi there")

    def test_variable_condition_comparison(self):
        source = "{% if user.role == expected %}yes{% else %}no{% endif %}"
        output = Template(source).render({"user": {"role": "admin"}, "expected": "admin"})
        self.assertEqual(output, "yes")

    def test_list_index_in_template(self):
        output = Template("{{ items.0 }}").render({"items": ["alpha", "beta"]})
        self.assertEqual(output, "alpha")

    def test_property_resolution_error_becomes_render_error(self):
        class Broken:
            @property
            def value(self):
                raise RuntimeError("boom")

        with self.assertRaises(RenderError):
            Template("{{ item.value }}").render({"item": Broken()})


if __name__ == "__main__":
    unittest.main()
