"""Test the parser."""

import unittest

from template_engine.errors import ParseError
from template_engine.lexer import lex
from template_engine.nodes import ForNode, IfNode, TemplateNode, VariableNode
from template_engine.parser import parse


class ParserTests(unittest.TestCase):
    def test_variable_template_parses(self):
        ast = parse(lex("Hello {{ name }}"))
        self.assertIsInstance(ast, TemplateNode)
        self.assertIsInstance(ast.children[1], VariableNode)

    def test_if_else_parses(self):
        ast = parse(lex("{% if user %}Hi{% else %}Bye{% endif %}"))
        self.assertIsInstance(ast.children[0], IfNode)
        self.assertEqual(len(ast.children[0].branches), 1)
        self.assertEqual(len(ast.children[0].else_body), 1)

    def test_for_loop_parses(self):
        ast = parse(lex("{% for user in users %}{{ user.name }}{% endfor %}"))
        self.assertIsInstance(ast.children[0], ForNode)
        self.assertEqual(ast.children[0].item_name, "user")

    def test_nested_blocks_parse(self):
        ast = parse(
            lex("{% for user in users %}{% if user.active %}{{ user.name }}{% endif %}{% endfor %}")
        )
        self.assertIsInstance(ast.children[0], ForNode)
        self.assertIsInstance(ast.children[0].body[0], IfNode)

    def test_unclosed_if_raises(self):
        with self.assertRaises(ParseError):
            parse(lex("{% if user %}Hi"))

    def test_unexpected_endif_raises(self):
        with self.assertRaises(ParseError):
            parse(lex("{% endif %}"))

    def test_malformed_for_raises(self):
        with self.assertRaises(ParseError):
            parse(lex("{% for user users %}{% endfor %}"))

    def test_set_block_parses(self):
        from template_engine.nodes import SetNode

        ast = parse(lex('{% set greeting = "Hi" %}{{ greeting }}'))
        self.assertIsInstance(ast.children[0], SetNode)
        self.assertEqual(ast.children[0].name, "greeting")


if __name__ == "__main__":
    unittest.main()
