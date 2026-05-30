"""Error classes for the template engine."""

from __future__ import annotations


class TemplateEngineError(Exception):
    """Base class for expected template engine errors."""

    def __init__(
        self,
        message: str,
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        location = ""
        if self.line is not None and self.column is not None:
            location = f" at line {self.line}, column {self.column}"
        elif self.line is not None:
            location = f" at line {self.line}"
        return f"{self.__class__.__name__}{location}: {self.message}"


class LexerError(TemplateEngineError):
    """Raised when source text cannot be tokenized."""


class ParseError(TemplateEngineError):
    """Raised when tokens cannot be parsed into an AST."""


class RenderError(TemplateEngineError):
    """Raised when rendering fails at runtime."""
