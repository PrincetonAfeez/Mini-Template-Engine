"""Test the context stack."""

import unittest

from template_engine.context import MISSING, ContextStack
from template_engine.errors import RenderError


class User:
    def __init__(self):
        self.name = "Princeton"
        self._secret = "hidden"

    def method(self):
        return "nope"


class ContextTests(unittest.TestCase):
    def test_dict_and_object_lookup(self):
        stack = ContextStack({"user": {"profile": User()}})
        self.assertEqual(stack.resolve(("user", "profile", "name")), "Princeton")

    def test_list_index_lookup(self):
        stack = ContextStack({"items": [{"name": "first"}, {"name": "second"}]})
        self.assertEqual(stack.resolve(("items", "0", "name")), "first")

    def test_missing_lenient_returns_sentinel(self):
        stack = ContextStack({}, strict=False)
        self.assertIs(stack.resolve(("missing",)), MISSING)

    def test_missing_strict_raises(self):
        stack = ContextStack({}, strict=True)
        with self.assertRaises(RenderError):
            stack.resolve(("missing",))

    def test_private_attribute_rejected(self):
        stack = ContextStack({"user": User()})
        with self.assertRaises(RenderError):
            stack.resolve(("user", "_secret"))

    def test_callable_rejected(self):
        stack = ContextStack({"user": User()})
        with self.assertRaises(RenderError):
            stack.resolve(("user", "method"))

    def test_child_scope_shadows_without_mutating_parent(self):
        context = {"name": "outer"}
        stack = ContextStack(context)
        stack.push({"name": "inner"})
        self.assertEqual(stack.resolve(("name",)), "inner")
        stack.pop()
        self.assertEqual(stack.resolve(("name",)), "outer")
        self.assertEqual(context["name"], "outer")


if __name__ == "__main__":
    unittest.main()
