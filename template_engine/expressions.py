"""Parser for the small expression language inside tags."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from .errors import ParseError

_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$|^\d+$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+[eE][+-]?\d+)|(?:\d+\.\d*[eE][+-]?\d+)|(?:\.\d+[eE][+-]?\d+))$"
)
_NOT_PREFIX_RE = re.compile(r"^not(?:\s+(.*))?$", re.DOTALL)


@dataclass(frozen=True)
class VariableExpression:
    path: tuple[str, ...]


@dataclass(frozen=True)
class LiteralExpression:
    value: Any


@dataclass(frozen=True)
class FilterCall:
    name: str
    args: tuple[Expression, ...]


@dataclass(frozen=True)
class FilterExpression:
    base: Expression
    filters: tuple[FilterCall, ...]


@dataclass(frozen=True)
class ConditionExpression:
    kind: str
    left: Expression
    right: Expression | None = None


Expression = LiteralExpression | VariableExpression | FilterExpression
ValueExpression = LiteralExpression | VariableExpression


def parse_variable_expression(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> Expression:
    """Parse a variable output expression, including filter chains."""

    parts = _split_top_level(text, "|", line=line, column=column)
    if not parts or not parts[0].strip():
        raise ParseError("expected expression", line=line, column=column)

    base = parse_value_expression(parts[0].strip(), line=line, column=column)
    filters: list[FilterCall] = []
    for filter_text in parts[1:]:
        filters.append(_parse_filter_call(filter_text.strip(), line=line, column=column))

    if filters:
        return FilterExpression(base=base, filters=tuple(filters))
    return base


def parse_value_expression(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> ValueExpression:
    text = text.strip()
    try:
        return LiteralExpression(parse_literal(text, line=line, column=column))
    except ParseError:
        if _is_path(text):
            segments = tuple(text.split("."))
            for segment in segments:
                if segment.startswith("_"):
                    raise ParseError(
                        f"path segment cannot start with '_': {segment!r}",
                        line=line,
                        column=column,
                    ) from None
            return VariableExpression(segments)
        raise ParseError(f"unsupported expression {text!r}", line=line, column=column) from None


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

    operator = _find_top_level_operator(text, ("==", "!="), line=line, column=column)
    if operator is not None:
        index, op = operator
        left_text = text[:index].strip()
        right_text = text[index + len(op) :].strip()
        left = parse_value_expression(left_text, line=line, column=column)
        right = parse_value_expression(right_text, line=line, column=column)
        return ConditionExpression(
            kind="equals" if op == "==" else "not_equals",
            left=left,
            right=right,
        )

    not_match = _NOT_PREFIX_RE.match(text)
    if not_match:
        target = (not_match.group(1) or "").strip()
        if not target:
            raise ParseError("expected expression after 'not'", line=line, column=column)
        return ConditionExpression(
            kind="not_truthy",
            left=parse_value_expression(target, line=line, column=column),
        )

    return ConditionExpression(
        kind="truthy",
        left=parse_value_expression(text, line=line, column=column),
    )


def parse_literal(
    text: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> Any:
    text = text.strip()
    if text == "true":
        return True
    if text == "false":
        return False
    if text in {"none", "null"}:
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

    args: list[Expression] = []
    if raw_args is not None and raw_args.strip():
        for arg_text in _split_top_level(raw_args, ",", line=line, column=column):
            args.append(parse_value_expression(arg_text.strip(), line=line, column=column))
    return FilterCall(name=name, args=tuple(args))


def _is_path(text: str) -> bool:
    if not text:
        return False
    return all(_PATH_SEGMENT_RE.match(part) for part in text.split("."))


def _split_top_level(
    text: str,
    separator: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> list[str]:
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
                raise ParseError("unbalanced ')' in expression", line=line, column=column)
            continue
        if char == separator and paren_depth == 0:
            parts.append(text[start:index])
            start = index + 1

    if quote is not None:
        raise ParseError("unclosed string literal in expression", line=line, column=column)
    if paren_depth != 0:
        raise ParseError("unbalanced '(' in expression", line=line, column=column)

    parts.append(text[start:])
    return parts


def _find_top_level_operator(
    text: str,
    operators: tuple[str, ...],
    *,
    line: int | None = None,
    column: int | None = None,
) -> tuple[int, str] | None:
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
            paren_depth -= 1
            if paren_depth < 0:
                raise ParseError("unbalanced ')' in expression", line=line, column=column)
            index += 1
            continue

        if paren_depth == 0:
            for operator in operators:
                if text.startswith(operator, index):
                    return index, operator
        index += 1

    if quote is not None:
        raise ParseError("unclosed string literal in expression", line=line, column=column)
    if paren_depth != 0:
        raise ParseError("unbalanced '(' in expression", line=line, column=column)
    return None
