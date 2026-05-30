"""Parser for the small expression language inside tags."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from .errors import ParseError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+[eE][+-]?\d+)|(?:\d+\.\d*[eE][+-]?\d+)|(?:\.\d+[eE][+-]?\d+))$"
)


@dataclass(frozen=True)
class VariableExpression:
    path: tuple[str, ...]


@dataclass(frozen=True)
class LiteralExpression:
    value: Any


@dataclass(frozen=True)
class FilterCall:
    name: str
    args: list[Any]


@dataclass(frozen=True)
class FilterExpression:
    base: Any
    filters: list[FilterCall]


@dataclass(frozen=True)
class ConditionExpression:
    kind: str
    left: Any
    right: Any | None = None


def parse_variable_expression(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> Any:
    """Parse a variable output expression, including filter chains."""

    parts = _split_top_level(text, "|")
    if not parts or not parts[0].strip():
        raise ParseError("expected expression", line=line, column=column)

    base = parse_value_expression(parts[0].strip(), line=line, column=column)
    filters: list[FilterCall] = []
    for filter_text in parts[1:]:
        filters.append(_parse_filter_call(filter_text.strip(), line=line, column=column))

    if filters:
        return FilterExpression(base=base, filters=filters)
    return base


def parse_value_expression(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> Any:
    text = text.strip()
    if _is_path(text):
        return VariableExpression(tuple(text.split(".")))
    try:
        return LiteralExpression(parse_literal(text, line=line, column=column))
    except ParseError:
        raise ParseError(f"unsupported expression {text!r}", line=line, column=column)


def parse_condition_expression(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> ConditionExpression:
    """Parse the deliberately small V1 condition grammar."""

    text = text.strip()
    if not text:
        raise ParseError("expected condition expression", line=line, column=column)

    operator = _find_top_level_operator(text, ("==", "!="))
    if operator is not None:
        index, op = operator
        left_text = text[:index].strip()
        right_text = text[index + len(op) :].strip()
        left = _parse_path_expression(left_text, line=line, column=column)
        right = LiteralExpression(parse_literal(right_text, line=line, column=column))
        return ConditionExpression(
            kind="equals" if op == "==" else "not_equals",
            left=left,
            right=right,
        )

    if text.startswith("not "):
        target = text[4:].strip()
        if not target:
            raise ParseError("expected expression after 'not'", line=line, column=column)
        return ConditionExpression(
            kind="not_truthy",
            left=_parse_path_expression(target, line=line, column=column),
        )

    return ConditionExpression(
        kind="truthy",
        left=_parse_path_expression(text, line=line, column=column),
    )


def parse_literal(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> Any:
    text = text.strip()
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    if len(text) >= 2 and text[0] in {'"', "'"} and text[-1] == text[0]:
        try:
            value = ast.literal_eval(text)
        except (SyntaxError, ValueError) as exc:
            raise ParseError(f"invalid string literal {text!r}", line=line, column=column) from exc
        if not isinstance(value, str):
            raise ParseError(f"invalid string literal {text!r}", line=line, column=column)
        return value
    raise ParseError(f"expected literal, got {text!r}", line=line, column=column)


def _parse_path_expression(
    text: str,
    *,
    line: int | None,
    column: int | None,
) -> VariableExpression:
    if not _is_path(text):
        raise ParseError(f"expected variable path, got {text!r}", line=line, column=column)
    return VariableExpression(tuple(text.split(".")))


def _parse_filter_call(
    text: str,
    *,
    line: int | None,
    column: int | None,
) -> FilterCall:
    if not text:
        raise ParseError("expected filter name", line=line, column=column)

    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\((.*)\))?", text, flags=re.DOTALL)
    if not match:
        raise ParseError(f"invalid filter syntax {text!r}", line=line, column=column)

    name, raw_args = match.groups()
    if name.startswith("_"):
        raise ParseError(f"invalid filter name {name!r}", line=line, column=column)

    args: list[Any] = []
    if raw_args is not None and raw_args.strip():
        for arg_text in _split_top_level(raw_args, ","):
            args.append(parse_literal(arg_text, line=line, column=column))
    return FilterCall(name=name, args=args)


def _is_path(text: str) -> bool:
    if not text:
        return False
    return all(_IDENTIFIER_RE.match(part) for part in text.split("."))


def _split_top_level(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    paren_depth = 0

    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {'"', "'"}:
            quote = char
            continue
        if char == "(":
            paren_depth += 1
            continue
        if char == ")":
            paren_depth -= 1
            if paren_depth < 0:
                paren_depth = 0
            continue
        if char == separator and paren_depth == 0:
            parts.append(text[start:index])
            start = index + 1

    parts.append(text[start:])
    return parts


def _find_top_level_operator(text: str, operators: tuple[str, ...]) -> tuple[int, str] | None:
    quote: str | None = None
    escaped = False
    paren_depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char in {'"', "'"}:
            quote = char
            index += 1
            continue
        if char == "(":
            paren_depth += 1
            index += 1
            continue
        if char == ")":
            paren_depth = max(0, paren_depth - 1)
            index += 1
            continue

        if paren_depth == 0:
            for operator in operators:
                if text.startswith(operator, index):
                    return index, operator
        index += 1
    return None
