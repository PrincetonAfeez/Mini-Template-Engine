"""Test _read_template without blocking on stdin."""

import io
import unittest
from unittest.mock import patch

from template_engine.cli import _read_template


class ReadTemplateTests(unittest.TestCase):
    def test_read_from_stdin(self):
        with patch("sys.stdin", io.StringIO("from stdin")):
            self.assertEqual(_read_template("-"), "from stdin")


if __name__ == "__main__":
    unittest.main()
