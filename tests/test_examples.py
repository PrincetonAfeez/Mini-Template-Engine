"""Integration tests for example templates."""

import json
import unittest
from pathlib import Path

from template_engine.template import Template

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class ExampleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((EXAMPLES / "context.json").read_text(encoding="utf-8"))

    def test_hello_template(self):
        source = (EXAMPLES / "hello.tmpl").read_text(encoding="utf-8")
        output = Template(source).render(self.context)
        self.assertEqual(output, "Hello, Princeton!\n")

    def test_conditions_template(self):
        source = (EXAMPLES / "conditions.tmpl").read_text(encoding="utf-8")
        output = Template(source).render(self.context)
        self.assertEqual(output, "\nWelcome back, admin.\n\n")

    def test_loop_template(self):
        source = (EXAMPLES / "loop.tmpl").read_text(encoding="utf-8")
        output = Template(source).render(self.context)
        self.assertEqual(output, "\n1. Ava\n\n2. Mia\n\n")

    def test_invoice_template(self):
        source = (EXAMPLES / "invoice.tmpl").read_text(encoding="utf-8")
        output = Template(source).render(self.context)
        self.assertIn("Invoice for Princeton", output)
        self.assertIn("design, build, test", output)
        self.assertIn("12.35", output)
        self.assertIn("Literal template marker: {{ not_rendered }}", output)

    def test_showcase_template(self):
        source = (EXAMPLES / "showcase.tmpl").read_text(encoding="utf-8")
        output = Template(source).render(self.context)
        self.assertIn("Invoice for Princeton", output)
        self.assertIn("- 1. Design", output)
        self.assertIn("VIP", output)
        self.assertIn("Documentation marker preserved: {{ not_rendered }}", output)


if __name__ == "__main__":
    unittest.main()
