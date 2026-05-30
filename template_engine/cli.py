"""Command-line interface for the mini template engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .debug import dump_ast, dump_tokens
from .errors import TemplateEngineError
from .expressions import parse_literal
from .template import Template


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    modes = [args.check, args.dump_tokens, args.dump_ast]
    if sum(1 for enabled in modes if enabled) > 1:
        parser.error("--check, --dump-tokens, and --dump-ast are mutually exclusive")

    try:
        source = _read_template(args.template)
        context = _read_context(args.context)
        for assignment in args.set_values:
            _apply_assignment(context, assignment)

        template = Template(
            source,
            strict=args.strict,
            autoescape=not args.no_autoescape,
        )

        if args.check:
            template.check()
            print("ok")
            return 0
        if args.dump_tokens:
            print(dump_tokens(template.tokens()))
            return 0
        if args.dump_ast:
            print(dump_ast(template.ast()))
            return 0

        output = template.render(context)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0

    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TemplateEngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary converts unexpected failures.
        print(f"internal error: {exc}", file=sys.stderr)
        return 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-engine")
    parser.add_argument("template", help="template path, or '-' to read from stdin")
    parser.add_argument("--context", help="JSON context file")
    parser.add_argument("--set", dest="set_values", action="append", default=[], help="inline key=value context value")
    parser.add_argument("-o", "--output", help="write rendered output to this file")
    parser.add_argument("--strict", action="store_true", help="raise when variables are missing")
    parser.add_argument("--no-autoescape", action="store_true", help="disable HTML autoescaping")
    parser.add_argument("--check", action="store_true", help="parse only and report syntax errors")
    parser.add_argument("--dump-tokens", action="store_true", help="print the token stream")
    parser.add_argument("--dump-ast", action="store_true", help="print the parsed AST")
    return parser


def _read_template(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _read_context(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("context JSON must contain an object")
    return value


def _apply_assignment(context: dict[str, Any], assignment: str) -> None:
    if "=" not in assignment:
        raise ValueError(f"invalid --set value {assignment!r}; expected key=value")
    key, raw_value = assignment.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError("invalid --set value; key cannot be empty")

    try:
        value = parse_literal(raw_value.strip())
    except TemplateEngineError:
        value = raw_value

    target = context
    parts = key.split(".")
    for part in parts[:-1]:
        if not part:
            raise ValueError(f"invalid --set key {key!r}")
        child = target.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"cannot assign nested key through non-object value {part!r}")
        target = child
    if not parts[-1]:
        raise ValueError(f"invalid --set key {key!r}")
    target[parts[-1]] = value


if __name__ == "__main__":
    raise SystemExit(main())
