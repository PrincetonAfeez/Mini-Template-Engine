"""Token contracts shared by the lexer and parser."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    TEXT = "TEXT"
    VARIABLE = "VARIABLE"
    BLOCK = "BLOCK"
    RAW = "RAW"
    COMMENT = "COMMENT"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    trim_left: bool = False
    trim_right: bool = False
