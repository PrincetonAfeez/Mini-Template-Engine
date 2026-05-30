"""Source scanner for template text."""

from __future__ import annotations

import bisect
import re
from collections.abc import Iterator

from .errors import LexerError
from .tokens import Token, TokenType

_ENDRAW_RE = re.compile(r"{%-?\s*endraw\s*-?%}", flags=re.IGNORECASE)


def lex(source: str, *, include_comments: bool = False) -> Iterator[Token]:
    """Tokenize template source.

    The implementation keeps a token list internally so whitespace trim markers
    can alter adjacent text tokens, while still exposing an iterator.
    """

    line_starts = _line_starts(source)
    tokens: list[Token] = []
    index = 0
    pending_trim_right = False

    def line_col(offset: int) -> tuple[int, int]:
        line_index = bisect.bisect_right(line_starts, offset) - 1
        return line_index + 1, offset - line_starts[line_index] + 1

    def emit_text(text: str, start: int) -> None:
        nonlocal pending_trim_right
        if not text:
            return
        if pending_trim_right:
            stripped = text.lstrip()
            start += len(text) - len(stripped)
            text = stripped
            pending_trim_right = False
        if not text:
            return
        line, column = line_col(start)
        tokens.append(Token(TokenType.TEXT, text, line, column))

    def trim_previous() -> None:
        if not tokens:
            return
        previous = tokens[-1]
        if previous.type not in {TokenType.TEXT, TokenType.RAW}:
            return
        trimmed = previous.value.rstrip()
        if trimmed:
            tokens[-1] = Token(
                previous.type,
                trimmed,
                previous.line,
                previous.column,
                previous.trim_left,
                previous.trim_right,
            )
        else:
            tokens.pop()

    while index < len(source):
        next_index, opener = _find_next_opener(source, index)
        if next_index == -1:
            emit_text(source[index:], index)
            index = len(source)
            break

        emit_text(source[index:next_index], index)
        start = next_index
        line, column = line_col(start)

        if opener == "{{":
            token, index = _read_tag(source, start, "}}", TokenType.VARIABLE, line, column)
            if token.trim_left:
                trim_previous()
            tokens.append(token)
            pending_trim_right = token.trim_right
            continue

        if opener == "{#":
            token, index = _read_tag(source, start, "#}", TokenType.COMMENT, line, column)
            if token.trim_left:
                trim_previous()
            if include_comments:
                tokens.append(token)
            pending_trim_right = token.trim_right
            continue

        token, next_after_block = _read_tag(source, start, "%}", TokenType.BLOCK, line, column)
        if token.trim_left:
            trim_previous()

        if token.value.strip().lower() == "raw":
            raw_start = next_after_block
            match = _ENDRAW_RE.search(source, raw_start)
            if match is None:
                raise LexerError("unterminated raw block", line=line, column=column)

            raw_text = source[raw_start : match.start()]
            if token.trim_right:
                raw_text = raw_text.lstrip()

            end_tag = match.group(0)
            end_trim_left = end_tag.startswith("{%-")
            end_trim_right = end_tag.rstrip().endswith("-%}")
            if end_trim_left:
                raw_text = raw_text.rstrip()

            tokens.append(Token(TokenType.RAW, raw_text, line, column))
            pending_trim_right = end_trim_right
            index = match.end()
            continue

        tokens.append(token)
        pending_trim_right = token.trim_right
        index = next_after_block

    eof_line, eof_column = line_col(len(source))
    tokens.append(Token(TokenType.EOF, "", eof_line, eof_column))
    yield from tokens


def _read_tag(
    source: str,
    start: int,
    closer: str,
    token_type: TokenType,
    line: int,
    column: int,
) -> tuple[Token, int]:
    content_start = start + 2
    trim_left = False
    if content_start < len(source) and source[content_start] == "-":
        trim_left = True
        content_start += 1

    close_index = source.find(closer, content_start)
    if close_index == -1:
        name = {
            TokenType.VARIABLE: "variable",
            TokenType.BLOCK: "block",
            TokenType.COMMENT: "comment",
        }.get(token_type, "tag")
        raise LexerError(f"unterminated {name} tag", line=line, column=column)

    value_end = close_index
    trim_right = False
    if value_end > content_start and source[value_end - 1] == "-":
        trim_right = True
        value_end -= 1

    value = source[content_start:value_end].strip()
    return Token(token_type, value, line, column, trim_left, trim_right), close_index + len(closer)


def _find_next_opener(source: str, start: int) -> tuple[int, str]:
    candidates: list[tuple[int, str]] = []
    for opener in ("{{", "{%", "{#"):
        index = source.find(opener, start)
        if index != -1:
            candidates.append((index, opener))
    if not candidates:
        return -1, ""
    return min(candidates, key=lambda item: item[0])


def _line_starts(source: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(source):
        if char == "\n":
            starts.append(index + 1)
    return starts
