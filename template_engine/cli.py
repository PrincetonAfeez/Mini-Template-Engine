"""Command-line interface for the mini template engine."""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

from ._version import __version__
from .debug import dump_ast, dump_tokens
from .errors import TemplateEngineError, format_error
from .expressions import parse_literal
from .filters import FilterRegistry, default_filter_registry
from .template import Template

logger = logging.getLogger(__name__)

_SET_KEY_SEGMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    _configure_logging(args.verbose)

    modes = [args.check, args.dump_tokens, args.dump_ast]
    if sum(1 for enabled in modes if enabled) > 1:
        parser.error("--check, --dump-tokens, and --dump-ast are mutually exclusive")

    source = ""
    try:
        source = _read_template(args.template)
        context = _read_context(args.context)
        for assignment in args.set_values:
            _apply_assignment(context, assignment)

        filters = default_filter_registry()
        if args.filter_module:
            filters.extend(_load_filter_registry(args.filter_module))

        started = time.perf_counter()
        template = Template(
            source,
            strict=args.strict,
            autoescape=not args.no_autoescape,
            filters=filters,
        )

        if args.check:
            template.check()
            if args.verbose:
                _print_stats(template, started)
            print("ok")
            return 0
        if args.dump_tokens:
            tokens = template.tokens(include_comments=args.include_comments)
            if args.verbose:
                logger.info("tokens=%s", len(tokens))
            print(dump_tokens(tokens))
            return 0
        if args.dump_ast:
            ast = template.ast()
            if args.verbose:
                _print_stats(template, started)
            print(dump_ast(ast))
            return 0

        output = template.render(context)
        if args.verbose:
            _print_stats(template, started, rendered=len(output))
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0

    except (OSError, ValueError, json.JSONDecodeError, ModuleNotFoundError, AttributeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TemplateEngineError as exc:
        print(format_error(exc, source), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary converts unexpected failures.
        print(f"internal error: {exc}", file=sys.stderr)
        return 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="template-engine")
    parser.add_argument("template", nargs="?", default="-", help="template path, or '-' to read from stdin")
    parser.add_argument("--context", help="JSON context file")
    parser.add_argument(
        "--set",
        dest="set_values",
        action="append",
        default=[],
        help="inline key=value context value",
    )
    parser.add_argument("-o", "--output", help="write rendered output to this file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="raise on missing variables and invalid loop iterables",
    )
    parser.add_argument("--no-autoescape", action="store_true", help="disable HTML autoescaping")
    parser.add_argument("--check", action="store_true", help="parse only and report syntax errors")
    parser.add_argument("--dump-tokens", action="store_true", help="print the token stream")
    parser.add_argument("--dump-ast", action="store_true", help="print the parsed AST")
    parser.add_argument(
        "--include-comments",
        action="store_true",
        help="include comment tokens when dumping the token stream",
    )
    parser.add_argument(
        "--filter-module",
        help="import path to a FilterRegistry or module:attribute providing one",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="log stage statistics to stderr")
    return parser


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(message)s",
        stream=sys.stderr,
        force=True,
    )


def _print_stats(template: Template, started: float, *, rendered: int | None = None) -> None:
    elapsed_ms = (time.perf_counter() - started) * 1000
    token_count = len(template.tokens())
    top_level_nodes = len(template.ast().children)
    message = f"tokens={token_count} top_level_nodes={top_level_nodes} time_ms={elapsed_ms:.2f}"
    if rendered is not None:
        message += f" output_chars={rendered}"
    logger.info(message)


def _load_filter_registry(spec: str) -> FilterRegistry:
    module_name, _, attr = spec.partition(":")
    attr = attr or "filter_registry"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(f"could not import filter module {module_name!r}") from exc
    try:
        registry = getattr(module, attr)
    except AttributeError as exc:
        raise AttributeError(f"module {module_name!r} has no attribute {attr!r}") from exc
    if not isinstance(registry, FilterRegistry):
        raise ValueError(f"{spec!r} did not resolve to a FilterRegistry")
    return registry


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
    for part in parts:
        if not _SET_KEY_SEGMENT_RE.match(part):
            raise ValueError(f"invalid --set key {key!r}")
    for part in parts[:-1]:
        child = target.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"cannot assign nested key through non-object value {part!r}")
        target = child
    target[parts[-1]] = value


if __name__ == "__main__":
    raise SystemExit(main())
