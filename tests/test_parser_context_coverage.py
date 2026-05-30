"""Parser and context coverage helpers."""

import unittest

from template_engine.context import ContextStack
from template_engine.errors import ParseError, RenderError
from template_engine.lexer import lex
from template_engine.parser import parse


class ParserContextCoverageTests(unittest.TestCase):
    def test_parse_eof_inside_if(self):
        with self.assertRaises(ParseError):
            parse(list(lex("{% if user %}")))

    def test_context_empty_path(self):
        from template_engine.context import MISSING

        stack = ContextStack({}, strict=False)
        self.assertIs(stack.resolve(tuple()), MISSING)

    def test_context_strict_missing_intermediate(self):
        stack = ContextStack({"user": {}}, strict=True)
        with self.assertRaises(RenderError):
            stack.resolve(("user", "missing", "name"))

    def test_context_lenient_missing_on_object_attr(self):
        class Obj:
            pass

        stack = ContextStack({"obj": Obj()}, strict=False)
        from template_engine.context import MISSING

        self.assertIs(stack.resolve(("obj", "missing")), MISSING)


if __name__ == "__main__":
    unittest.main()
