""" Test the filter registry. """

import unittest

from template_engine.context import MISSING
from template_engine.errors import RenderError
from template_engine.escape import SafeString
from template_engine.filters import FilterRegistry, default_filter_registry


class FilterTests(unittest.TestCase):
    def test_built_in_filters(self):
        registry = default_filter_registry()
        self.assertEqual(registry.apply("upper", "hi"), "HI")
        self.assertEqual(registry.apply("trim", " hi "), "hi")
        self.assertEqual(registry.apply("default", MISSING, "N/A"), "N/A")
        self.assertEqual(registry.apply("length", [1, 2, 3]), 3)
        self.assertEqual(registry.apply("join", ["a", "b"], ", "), "a, b")
        self.assertEqual(registry.apply("round", 1.234, 2), 1.23)

    def test_safe_and_escape(self):
        registry = default_filter_registry()
        self.assertIsInstance(registry.apply("safe", "<b>x</b>"), SafeString)
        self.assertEqual(registry.apply("escape", "<b>x</b>"), "&lt;b&gt;x&lt;/b&gt;")

    def test_unknown_filter_raises(self):
        registry = default_filter_registry()
        with self.assertRaises(RenderError):
            registry.apply("missing", "x")

    def test_custom_filter_registration(self):
        registry = FilterRegistry()
        registry.register("bracket", lambda value: f"[{value}]")
        self.assertEqual(registry.apply("bracket", "x"), "[x]")


if __name__ == "__main__":
    unittest.main()
