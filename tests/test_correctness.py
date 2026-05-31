"""Additional correctness tests from grading phase 2."""

import unittest

from template_engine.errors import RenderError
from template_engine.template import Template


class CorrectnessTests(unittest.TestCase):
    def test_dict_loop_keys(self):
        output = Template("{% for key in mapping %}{{ key }}:{% endfor %}").render({"mapping": {"x": 1, "y": 2}})
        self.assertEqual(output, "x:y:")

    def test_default_vs_default_if_none(self):
        default_out = Template('{{ value | default("fallback") }}').render({"value": ""})
        if_none_out = Template('{{ value | default_if_none("fallback") }}').render({"value": ""})
        self.assertEqual(default_out, "fallback")
        self.assertEqual(if_none_out, "")

    def test_set_shadows_outer_scope_without_mutation(self):
        context = {"name": "outer"}
        output = Template("{{ name }}{% set name = 'inner' %}{{ name }}").render(context)
        self.assertEqual(output, "outerinner")
        self.assertEqual(context["name"], "outer")

    def test_set_inside_loop_scope(self):
        source = "{% for item in items %}{% set label = item %}{{ label }}{% endfor %}"
        output = Template(source).render({"items": ["a", "b"]})
        self.assertEqual(output, "ab")

    def test_index_out_of_range_lenient(self):
        output = Template("{{ items.99 }}").render({"items": ["only"]})
        self.assertEqual(output, "")

    def test_index_out_of_range_strict(self):
        with self.assertRaises(RenderError):
            Template("{{ items.99 }}", strict=True).render({"items": ["only"]})

    def test_template_tokens_include_comments(self):
        template = Template("{# c #}x")
        types = [token.type.value for token in template.tokens(include_comments=True)]
        self.assertIn("COMMENT", types)


if __name__ == "__main__":
    unittest.main()
