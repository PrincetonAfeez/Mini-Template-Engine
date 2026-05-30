"""Tests targeting debug dump coverage."""

import unittest

from template_engine.debug import dump_ast, dump_tokens
from template_engine.template import Template


class DebugDumpTests(unittest.TestCase):
    def test_dump_if_for_and_filters(self):
        source = (
            '{% if user %}{% set label = "x" %}'
            "{{ label | default('n') }}"
            "{% else %}no{% endif %}"
            "{% for item in items %}{{ item.0 }}{% endfor %}"
        )
        template = Template(source)
        ast_dump = dump_ast(template.ast())
        self.assertIn("IfNode", ast_dump)
        self.assertIn("Else", ast_dump)
        self.assertIn("SetNode", ast_dump)
        self.assertIn("ForNode", ast_dump)
        self.assertIn("default", ast_dump)

    def test_dump_condition_expressions(self):
        source = (
            "{% if not user %}{% elif user.role == 'admin' %}"
            "{% elif flag != false %}{% endif %}"
        )
        dump = dump_ast(Template(source).ast())
        self.assertIn("not user", dump)
        self.assertIn("==", dump)
        self.assertIn("!=", dump)

    def test_dump_tokens_with_trim_flags(self):
        dump = dump_tokens(list(Template("a {{- x -}} b").tokens()))
        self.assertIn("trim_left", dump)
        self.assertIn("trim_right", dump)


if __name__ == "__main__":
    unittest.main()
