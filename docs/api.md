# API Reference

## Package entry points

```python
from template_engine import (
    Template,
    FilterRegistry,
    SafeString,
    __version__,
    LexerError,
    ParseError,
    RenderError,
    format_error,
    default_filter_registry,
)
```

## `Template`

```python
Template(
    source: str,
    *,
    strict: bool = False,
    autoescape: bool = True,
    filters: FilterRegistry | None = None,
)
```

| Method | Description |
|--------|-------------|
| `tokens(*, include_comments=False)` | Lex the source and return tokens |
| `ast()` | Parse and cache the AST |
| `check()` | Validate syntax; returns `self` |
| `render(context=None)` | Render to `str` |

## `FilterRegistry`

| Method | Description |
|--------|-------------|
| `register(name, function)` | Add a filter callable |
| `get(name)` | Return a registered filter callable |
| `apply(name, value, *args)` | Run a filter |
| `extend(other)` | Copy filters from another registry |
| `items()` | Return registered filter name/callable pairs |
| `all_filters()` | Return a copy of the registered filter map |

## AST schema

`Template.ast()` returns a `TemplateNode` — the root of a tree of immutable dataclasses
defined in `template_engine.nodes`.

| Node | Fields | Role |
|------|--------|------|
| `TemplateNode` | `children: list[ASTNode]` | Root container |
| `TextNode` | `text`, `line`, `column` | Literal text output |
| `VariableNode` | `expression`, `line`, `column` | `{{ ... }}` output tag |
| `RawNode` | `text`, `line`, `column` | Literal text from `{% raw %}` |
| `IfNode` | `branches`, `else_body`, `line`, `column` | Conditional block |
| `ForNode` | `item_name`, `iterable_expression`, `body`, `line`, `column` | Loop block |
| `SetNode` | `name`, `expression`, `line`, `column` | `{% set %}` assignment |

`IfNode.branches` is a list of `IfBranch(condition, body)` pairs. Variable output and
loop/set expressions use the small expression types in `template_engine.expressions`
(for example `VariableExpression`, `FilterExpression`, `LiteralExpression`).

Use `template_engine.debug.dump_ast()` for a human-readable tree when debugging.

## Built-in filters

| Filter | Description |
|--------|-------------|
| `upper`, `lower`, `title`, `trim` | String transforms |
| `default(fallback="")` | Fallback when missing, `None`, or `""` |
| `default_if_none(fallback="")` | Fallback only for missing/`None` |
| `length` | `len()` of value |
| `join(separator="")` | Join iterables (not strings) |
| `round(ndigits=0)` | Numeric rounding |
| `escape` | HTML escape → `SafeString` |
| `safe` | Mark trusted HTML |

## Errors

All engine errors inherit from `TemplateEngineError` and expose
`message`, `line`, and `column`.

```python
from template_engine import format_error

try:
    Template("{{ x }", strict=True).render({})
except RenderError as exc:
    print(format_error(exc, source="{{ x }}"))
```

## CLI

```
template-engine [-h] [--version] [-v] [--context CONTEXT]
                [--set SET_VALUES] [-o OUTPUT] [--strict]
                [--no-autoescape] [--check] [--dump-tokens]
                [--dump-ast] [--include-comments]
                [--filter-module FILTER_MODULE]
                [template]
```

Exit codes: `0` success, `1` template error, `2` usage/IO error, `3` internal error.

## Lower-level modules

Advanced use (tests, tooling):

- `template_engine.lexer.lex(source)`
- `template_engine.parser.parse(tokens)`
- `template_engine.renderer.Renderer`
- `template_engine.expressions.parse_variable_expression(text)`
- `template_engine.debug.dump_tokens` / `dump_ast`
