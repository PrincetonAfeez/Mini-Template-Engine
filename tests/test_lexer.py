"""Test the lexer."""

import unittest

from template_engine.errors import LexerError
from template_engine.lexer import lex
from template_engine.tokens import TokenType


class LexerTests(unittest.TestCase):
    def test_mixed_text_variable_and_block_tokens(self):
        tokens = list(lex("Hello {{ name }}!{% if user %}x{% endif %}"))

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.TEXT,
                TokenType.VARIABLE,
                TokenType.TEXT,
                TokenType.BLOCK,
                TokenType.TEXT,
                TokenType.BLOCK,
                TokenType.EOF,
            ],
        )
        self.assertEqual(tokens[1].value, "name")
        self.assertEqual(tokens[3].value, "if user")

    def test_comments_are_stripped(self):
        tokens = list(lex("Hello {# hidden #} world"))
        self.assertEqual([token.type for token in tokens], [TokenType.TEXT, TokenType.TEXT, TokenType.EOF])
        self.assertEqual("".join(token.value for token in tokens if token.type == TokenType.TEXT), "Hello  world")

    def test_raw_block_preserves_inner_markers(self):
        tokens = list(lex("{% raw %}{{ name }}{% endraw %}"))
        self.assertEqual(tokens[0].type, TokenType.RAW)
        self.assertEqual(tokens[0].value, "{{ name }}")

    def test_line_and_column_are_tracked(self):
        tokens = list(lex("Hello\n{{ name }}"))
        self.assertEqual(tokens[1].line, 2)
        self.assertEqual(tokens[1].column, 1)

    def test_unterminated_variable_raises(self):
        with self.assertRaises(LexerError):
            list(lex("Hello {{ name"))

    def test_whitespace_trim_markers(self):
        tokens = list(lex("Hello {{- name -}} !"))
        text = "".join(token.value for token in tokens if token.type == TokenType.TEXT)
        self.assertEqual(text, "Hello!")

    def test_endraw_requires_lowercase(self):
        with self.assertRaises(LexerError):
            list(lex("{% raw %}{{ name }}{% ENDRAW %}"))

    def test_include_comments_flag(self):
        tokens = list(lex("{# hidden #}", include_comments=True))
        self.assertEqual(tokens[0].type, TokenType.COMMENT)


if __name__ == "__main__":
    unittest.main()
