""" Test the template facade. """

import unittest

from template_engine.nodes import TemplateNode
from template_engine.template import Template
from template_engine.tokens import TokenType


class TemplateFacadeTests(unittest.TestCase):
    def test_tokens_ast_check_and_repeated_render(self):
        template = Template("Hello {{ name }}")
        self.assertEqual(template.tokens()[0].type, TokenType.TEXT)
        self.assertIsInstance(template.ast(), TemplateNode)
        self.assertIsNone(template.check())
        self.assertEqual(template.render({"name": "A"}), "Hello A")
        self.assertEqual(template.render({"name": "B"}), "Hello B")


if __name__ == "__main__":
    unittest.main()
