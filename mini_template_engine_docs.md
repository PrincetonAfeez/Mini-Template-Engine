# Architecture Decision Record
## App — Mini Template Engine
**Template Rendering Group | Document 1 of 5**
**Status: Accepted**

---

## Context

Mini Template Engine is a pure-Python, Jinja-inspired template engine designed to demonstrate a compiler-style pipeline: source text is tokenized, parsed into an immutable AST, and rendered by a recursive tree-walking renderer. The project intentionally focuses on language fundamentals rather than framework breadth. It supports variables, literals, filters, `{% set %}`, conditionals, loops, raw blocks, comments, whitespace trimming, HTML autoescaping, CLI rendering, syntax checking, token dumping, AST dumping, and custom filter registries.

The app is not a full Jinja replacement. It does not support arbitrary Python expressions, `eval`, method calls, property getters, includes, macros, template inheritance, or multi-file loading. The engine is designed as a library core first, with a CLI wrapper for demonstrations, grading, debugging, and portfolio presentation.

Primary architectural pipeline:

```text
Template source
  -> lexer
  -> token stream
  -> parser
  -> immutable AST
  -> renderer
  -> output
```

---

## Decisions

### Decision 1 — Build a compiler-style pipeline

**Chosen:** Separate the engine into lexer, token model, parser, AST node dataclasses, expression parser, renderer, context stack, filters, escaping, debug dumps, and CLI.

**Rejected:** A single regex-based render function.

**Rationale:** A template engine becomes hard to extend when tokenization, syntax validation, and rendering are mixed together. A staged pipeline makes each boundary inspectable and testable. It also demonstrates foundational compiler/interpreter skills.

---

### Decision 2 — Use a tree-walking renderer

**Chosen:** Render the AST recursively at runtime.

**Rejected:** Bytecode, compiled Python, or generated code.

**Rationale:** Tree walking is transparent and appropriate for a mini engine. It keeps the implementation explainable, avoids code generation risk, and makes security constraints easier to enforce. Performance is acceptable for the intended scope.

---

### Decision 3 — Keep the expression grammar deliberately small

**Chosen:** Support literals, ASCII dotted paths, filters, truthiness, `not`, `==`, and `!=`.

**Rejected:** Arbitrary Python expressions, `and` / `or`, arithmetic, function calls, indexing syntax beyond dotted numeric path segments, and `eval`.

**Rationale:** The engine is meant to render templates safely, not execute Python. A small grammar reduces the attack surface and makes parser behavior predictable.

---

### Decision 4 — Use immutable dataclasses for AST and expression nodes

**Chosen:** Nodes and expressions are frozen dataclasses.

**Rejected:** Mutable dictionaries or dynamic node objects.

**Rationale:** Immutable nodes make the parse result stable, cacheable, easier to inspect, and safer to pass between components. They also provide clear type contracts.

---

### Decision 5 — Autoescape HTML by default

**Chosen:** Variable output is HTML-escaped unless a value is already a `SafeString` or passes through the `safe` filter.

**Rejected:** Escaping only on explicit `escape` filter.

**Rationale:** Secure defaults are important for a template engine. Users must opt out of escaping for trusted HTML instead of remembering to opt in for unsafe values.

---

### Decision 6 — Prevent callable, private, property, and descriptor access

**Chosen:** Context resolution rejects private names, callable results, property access, cached property access, and descriptor access.

**Rejected:** Allowing normal Python attribute semantics.

**Rationale:** Normal Python attribute lookup can run code or expose unsafe internals. The engine is intentionally data-oriented. Templates may read mappings, sequences, simple instance values, and loop metadata, but not execute application behavior.

---

### Decision 7 — Make filters explicit through a registry

**Chosen:** Built-ins are registered in `FilterRegistry`, and custom filters are loaded by extending registries.

**Rejected:** Looking up filters from globals or allowing arbitrary function calls from templates.

**Rationale:** A registry provides a controlled extension point. It keeps the expression grammar small while still allowing user-defined transformations.

---

### Decision 8 — Keep templates single-file

**Chosen:** No includes, macros, inheritance, or loader abstraction in V1.

**Rejected:** Multi-file template loading.

**Rationale:** Single-file rendering keeps scope aligned with the learning goal: lexing, parsing, AST design, and safe rendering. Multi-file features would require path security, loader semantics, recursion limits, cache invalidation, and dependency tracking.

---

### Decision 9 — Expose a simple `Template` facade

**Chosen:** `Template` owns source text, token caching, AST caching, syntax checking, and rendering.

**Rejected:** Forcing users to manually call `lex()`, `parse()`, and `Renderer()` for normal library use.

**Rationale:** The internal pipeline remains accessible, but the public API should be easy to use. `Template` gives library users a clean entry point without hiding the architecture.

---

### Decision 10 — Add CLI debug modes

**Chosen:** CLI supports `--check`, `--dump-tokens`, `--dump-ast`, `--context`, `--set`, `--filter-module`, `--strict`, `--no-autoescape`, `--output`, and verbose stats.

**Rejected:** CLI render-only behavior.

**Rationale:** This is a portfolio and academic project. Debug modes make the compiler pipeline visible to reviewers and help users understand syntax failures.

---

## Consequences

**Positive:**
- The architecture is easy to explain and inspect.
- Lexer, parser, renderer, context resolution, filters, and CLI can be tested separately.
- Secure defaults are built into rendering and lookup behavior.
- The project demonstrates real language-tooling concepts.
- The public API remains simple through `Template`.
- CLI debug commands make internal state visible without changing code.

**Negative / Trade-offs:**
- Tree walking is slower than compiled templates.
- No includes, macros, inheritance, or template loader.
- The expression grammar is intentionally limited.
- Conditions do not support `and` / `or`.
- Filters are functions, but templates cannot call arbitrary functions.
- For loops materialize iterables as lists to support loop metadata.
- Autoescaping is HTML-oriented and not context-aware by attribute/script/style location.

---

## Alternatives Not Explored

- Bytecode compiler.
- Python code generation.
- Full Jinja compatibility.
- Context-aware HTML escaping.
- Directory template loader.
- Template inheritance.
- Streaming renderer.
- Async rendering.
- Sandboxed Python expression evaluator.
- Template caching across files.

---

*Constitution reference: Article 1 (fundamentals and architectural thinking), Article 3.3 (scope discipline), Article 4 (quality proportional to scope), Article 5 (trade-offs), Article 6 (verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Mini Template Engine
**Template Rendering Group | Document 2 of 5**

---

## Overview

Mini Template Engine is a library plus CLI that renders text templates using a custom lexer, parser, expression system, AST, context stack, filter registry, and recursive renderer.

**Package:** `template_engine`  
**Console script:** `template-engine`  
**Python requirement:** `>=3.10`  
**Runtime dependencies:** none  
**Development tools:** pytest, coverage, hypothesis, mypy, ruff, pre-commit, build, twine  
**Primary public API:** `Template`, `FilterRegistry`, `default_filter_registry`, `SafeString`

---

## System Context

```text
User / CLI / Python code
  |
  v
Template(source)
  |
  +--> tokens() -> lexer.lex()
  |
  +--> ast() -> parser.parse()
  |
  +--> render(context) -> Renderer.render()
                              |
                              +--> ContextStack
                              +--> FilterRegistry
                              +--> HTML escaping
```

---

## Runtime Pipeline

```text
source string
  |
  v
lex(source)
  |
  +--> Token(TEXT)
  +--> Token(VARIABLE)
  +--> Token(BLOCK)
  +--> Token(RAW)
  +--> Token(COMMENT) optional
  +--> Token(EOF)
  |
  v
parse(tokens)
  |
  +--> TemplateNode
        +--> TextNode
        +--> VariableNode
        +--> RawNode
        +--> IfNode / IfBranch
        +--> ForNode
        +--> SetNode
  |
  v
Renderer(strict, autoescape, filters).render(ast, context)
  |
  +--> resolve dotted paths through ContextStack
  +--> evaluate literals, filters, and conditions
  +--> render loop scopes with LoopHelper
  +--> escape output unless SafeString
  |
  v
rendered text
```

---

## Module-Level Structure

```text
template_engine/
  __init__.py
  __main__.py
  _version.py
  cli.py
  context.py
  debug.py
  errors.py
  escape.py
  expressions.py
  filters.py
  lexer.py
  nodes.py
  parser.py
  renderer.py
  template.py
  tokens.py
  py.typed
```

---

## Key Components

### Token model

`tokens.py` defines:

```python
class TokenType(str, Enum):
    TEXT
    VARIABLE
    BLOCK
    RAW
    COMMENT
    EOF
```

`Token` stores:
- type
- value
- line
- column
- trim_left
- trim_right

---

### Lexer

`lexer.lex(source, include_comments=False)` scans source text and emits tokens.

Responsibilities:
- recognize `{{ ... }}` variables
- recognize `{% ... %}` blocks
- recognize `{# ... #}` comments
- handle `{% raw %} ... {% endraw %}`
- track line and column numbers
- support `-{%` / `-%}` style trim markers
- append EOF token
- raise `LexerError` for unterminated tags or raw blocks

Important behavior:
- trim-left can retroactively strip the previous text token
- trim-right affects the next text emission
- comments are skipped unless `include_comments=True`
- raw blocks emit literal text as `RAW`

---

### Expression parser

`expressions.py` defines a small expression model:
- `VariableExpression`
- `LiteralExpression`
- `FilterCall`
- `FilterExpression`
- `ConditionExpression`

Supported values:
- booleans: `true`, `false`
- null: `none`, `null`
- integers
- floats
- quoted strings
- ASCII dotted paths
- numeric path segments for sequence access
- filter chains with literal/path arguments

Supported conditions:
- truthiness
- `not`
- equality `==`
- inequality `!=`

Rejected:
- `and`
- `or`
- arbitrary Python
- unsupported expressions
- private path segments starting with `_`
- invalid filter names starting with `_`

---

### AST nodes

`nodes.py` defines immutable AST dataclasses:
- `TemplateNode`
- `TextNode`
- `VariableNode`
- `RawNode`
- `IfBranch`
- `IfNode`
- `ForNode`
- `SetNode`

The AST represents template structure after parsing and before rendering.

---

### Parser

`parser.py` performs recursive-descent parsing.

Responsibilities:
- turn token streams into `TemplateNode`
- parse variables into expressions
- parse `{% if %}`, `{% elif %}`, `{% else %}`, `{% endif %}`
- parse `{% for item in items %}` and `{% endfor %}`
- parse `{% set name = expression %}`
- enforce block nesting with stop tags
- reject unexpected end tags and unknown block tags
- report line/column-aware `ParseError`

---

### Context stack

`context.py` owns runtime variable resolution.

Components:
- `MissingValue`
- `MISSING`
- `LoopHelper`
- `ContextStack`

Responsibilities:
- maintain lexical scopes
- assign variables for `{% set %}`
- push loop scopes
- resolve dotted paths
- resolve mapping keys
- resolve sequence numeric segments
- resolve safe instance attributes
- reject private names
- reject callable results
- reject property/cached_property access
- reject descriptors
- return `MISSING` in lenient mode
- raise `RenderError` in strict mode

---

### Renderer

`renderer.py` walks the AST and produces text.

Responsibilities:
- render text and raw nodes directly
- evaluate variable expressions
- evaluate set statements
- evaluate if/elif/else branches
- render for loops
- add `loop.index`, `loop.index0`, `loop.first`, `loop.last`, and `loop.length`
- apply filters
- stringify values
- autoescape HTML by default
- preserve `SafeString`
- raise `RenderError` on runtime failures

---

### Filter registry

`filters.py` defines `FilterRegistry` and default filters.

Default filters:
- `upper`
- `lower`
- `title`
- `trim`
- `default`
- `default_if_none`
- `length`
- `join`
- `round`
- `escape`
- `safe`

Important behavior:
- filter names must be identifiers and cannot start with `_`
- unknown filters raise `RenderError`
- filter exceptions are wrapped as `RenderError`
- `safe` returns `SafeString`
- string transforms preserve safety when input is already safe

---

### Escaping

`escape.py` defines:
- `SafeString`
- `escape_html(value)`
- `mark_safe(value)`

Escaping uses Python's standard `html.escape(..., quote=True)`.

---

### Template facade

`template.py` defines `Template`.

Responsibilities:
- store source string
- cache tokens per comment mode
- cache parsed AST
- expose `check()`
- expose `render(context)`
- construct `Renderer` with strict, autoescape, and filters options

---

### CLI

`cli.py` defines the `template-engine` command.

Core commands/modes:
- render template
- `--check`
- `--dump-tokens`
- `--dump-ast`
- `--include-comments`
- `--context`
- `--set`
- `--output`
- `--strict`
- `--no-autoescape`
- `--filter-module`
- `--version`
- `--verbose`

Exit contract:
- `0`: success
- `1`: template engine error
- `2`: I/O, JSON, value, import, or attribute error
- `3`: unexpected internal error

---

## Data Structures

### `Token`

```python
@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    trim_left: bool = False
    trim_right: bool = False
```

---

### `TemplateNode`

```python
@dataclass(frozen=True)
class TemplateNode:
    children: tuple[ASTNode, ...]
```

---

### `VariableExpression`

```python
@dataclass(frozen=True)
class VariableExpression:
    path: tuple[str, ...]
```

---

### `FilterExpression`

```python
@dataclass(frozen=True)
class FilterExpression:
    base: Expression
    filters: tuple[FilterCall, ...]
```

---

### `LoopHelper`

```python
@dataclass(frozen=True)
class LoopHelper:
    index: int
    index0: int
    first: bool
    last: bool
    length: int
```

---

## Error Handling

Expected engine errors inherit from `TemplateEngineError`:
- `LexerError`
- `ParseError`
- `RenderError`

Each expected engine error can carry:
- message
- line
- column

`format_error()` can include a source excerpt and caret pointer.

---

## Security Controls

The engine avoids common template risks by:
- not using `eval`
- using a small expression grammar
- rejecting private path segments
- rejecting callables
- rejecting property and cached-property access
- rejecting descriptors
- autoescaping by default
- requiring explicit `safe` for trusted HTML
- keeping includes/macros out of scope
- using controlled filter registries

---

## Performance Notes

Documented complexity:
- lex: `O(n)`
- parse: `O(n)`
- render: `O(nodes)`

Known performance trade-off:
- `for` loops materialize iterables into lists to support `loop.length` and `loop.last`.

---

## Verification

The project configures:
- strict mypy for `template_engine`
- Ruff linting
- Ruff format check
- coverage fail-under 95
- pytest tests
- CI on Ubuntu and Windows
- Python 3.10 through 3.14

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Mini Template Engine
**Template Rendering Group | Document 3 of 5**

---

## Public Python API

### Primary import

```python
from template_engine import Template
```

### Extended imports

```python
from template_engine import (
    FilterRegistry,
    SafeString,
    default_filter_registry,
    LexerError,
    ParseError,
    RenderError,
    TemplateEngineError,
    format_error,
)
```

The package also exports AST node types for inspection/debugging.

---

## `Template` Constructor

```python
Template(
    source: str,
    *,
    strict: bool = False,
    autoescape: bool = True,
    filters: FilterRegistry | None = None,
)
```

### Arguments

| Argument | Type | Default | Description |
|---|---|---:|---|
| `source` | `str` | required | Template source text |
| `strict` | `bool` | `False` | Raise on missing variables and invalid loop iterables |
| `autoescape` | `bool` | `True` | HTML-escape variable output by default |
| `filters` | `FilterRegistry | None` | `None` | Custom registry; defaults to built-ins |

---

## `Template` Methods

### `tokens(include_comments=False)`

Returns a list of `Token` objects. Caches internally, returns a copy.

```python
tokens = Template("Hi {{ name }}").tokens()
```

---

### `ast()`

Parses and returns a cached `TemplateNode`.

```python
tree = Template("Hi {{ name }}").ast()
```

---

### `check()`

Parses the template and returns `self` if valid.

```python
Template("{% if user %}Hi{% endif %}").check()
```

---

### `render(context=None)`

Renders the template with a dictionary context.

```python
Template("Hello, {{ user.name | title }}!").render(
    {"user": {"name": "princeton"}}
)
```

---

## Template Syntax

### Variable output

```jinja
{{ user.name }}
{{ user.name | title }}
{{ price | round(2) }}
```

---

### Literals

Supported:
```jinja
{{ "hello" }}
{{ 'hello' }}
{{ 42 }}
{{ 3.14 }}
{{ true }}
{{ false }}
{{ none }}
{{ null }}
```

---

### Filters

```jinja
{{ name | upper }}
{{ name | default("Anonymous") }}
{{ items | join(", ") }}
{{ html | safe }}
{{ value | escape }}
```

Built-ins:
- `upper`
- `lower`
- `title`
- `trim`
- `default`
- `default_if_none`
- `length`
- `join`
- `round`
- `escape`
- `safe`

---

### Set

```jinja
{% set label = "Customer" %}
{{ label }}
```

---

### If / elif / else

```jinja
{% if user %}
  Hello {{ user.name }}
{% elif fallback %}
  Hello guest
{% else %}
  Missing user
{% endif %}
```

Supported conditions:
```jinja
{% if value %}
{% if not value %}
{% if status == "active" %}
{% if status != "disabled" %}
```

Unsupported:
```jinja
{% if a and b %}
{% if a or b %}
```

---

### For loop

```jinja
{% for item in items %}
  {{ loop.index }}. {{ item.name }}
{% endfor %}
```

Loop metadata:
- `loop.index`
- `loop.index0`
- `loop.first`
- `loop.last`
- `loop.length`

Rules:
- strings are rejected as loop iterables
- missing or invalid iterables render empty in lenient mode
- strict mode raises `RenderError`

---

### Raw block

```jinja
{% raw %}
Literal {{ not_rendered }}
{% endraw %}
```

---

### Comments

```jinja
{# this is ignored #}
```

Comment tokens can be included only for token dumps.

---

### Whitespace trimming

```jinja
{{- value -}}
{%- if user -%}
...
{%- endif -%}
```

---

## Variable Resolution Contract

Supported:
- mapping keys
- sequence numeric path segments
- simple instance attributes from `vars(obj)`
- non-callable class values
- loop helper fields

Rejected:
- path segments beginning with `_`
- callable values
- method calls
- property access
- cached property access
- descriptor access

---

## HTML Escaping Contract

Default:
```python
Template("{{ value }}").render({"value": "<b>x</b>"})
```

Expected:
```html
&lt;b&gt;x&lt;/b&gt;
```

Trusted HTML:
```jinja
{{ value | safe }}
```

Explicit escaping:
```jinja
{{ value | escape }}
```

Disable globally:
```python
Template("{{ value }}", autoescape=False)
```

or CLI:
```bash
template-engine template.tmpl --no-autoescape
```

---

## Custom Filter Contract

```python
from template_engine import FilterRegistry, Template, default_filter_registry

registry = default_filter_registry()
registry.register("shout", lambda value: str(value).upper() + "!")

Template("{{ name | shout }}", filters=registry).render({"name": "hi"})
```

Rules:
- filter name must be a valid identifier
- filter name cannot start with `_`
- exceptions become `RenderError`
- registry can extend another registry

---

## CLI Interface

### Command form

```bash
template-engine [template] [options]
```

`template` defaults to `-`, which reads from stdin.

---

## CLI Options

| Option | Description |
|---|---|
| `--context PATH` | Load JSON object context |
| `--set KEY=VALUE` | Add inline context value; repeatable |
| `-o`, `--output PATH` | Write rendered output to file |
| `--strict` | Raise on missing variables / invalid loop iterables |
| `--no-autoescape` | Disable HTML escaping |
| `--check` | Parse only and print `ok` |
| `--dump-tokens` | Print token stream |
| `--dump-ast` | Print parsed AST |
| `--include-comments` | Include comments when dumping tokens |
| `--filter-module SPEC` | Load external `FilterRegistry` |
| `--version` | Print version |
| `-v`, `--verbose` | Print stage stats to stderr |

`--check`, `--dump-tokens`, and `--dump-ast` are mutually exclusive.

---

## CLI Examples

### Render from file

```bash
template-engine examples/hello.tmpl --context examples/context.json
```

---

### Render from stdin

```bash
echo "Hello {{ name }}" | template-engine - --set name=Princeton
```

---

### Syntax check

```bash
template-engine examples/conditions.tmpl --check
```

Expected:
```text
ok
```

---

### Dump tokens

```bash
template-engine examples/invoice.tmpl --dump-tokens
```

---

### Dump AST

```bash
template-engine examples/invoice.tmpl --dump-ast
```

---

### Inline context values

```bash
template-engine examples/hello.tmpl --set user.name=Princeton --set count=3
```

Literal parsing is attempted first. If literal parsing fails, the raw string is used.

---

### Load custom filters

```bash
template-engine template.tmpl --filter-module my_module
template-engine template.tmpl --filter-module my_module:my_registry
```

The resolved object must be a `FilterRegistry`.

---

## CLI Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Lexer, parser, or render error |
| `2` | I/O, JSON, value, import, or attribute error |
| `3` | Unexpected internal error |

---

## Side Effects

| Operation | Side Effect |
|---|---|
| `Template.render()` | Pure in-memory rendering |
| CLI render | Reads template/context, writes stdout or output file |
| `--dump-tokens` | Prints token stream |
| `--dump-ast` | Prints AST dump |
| `--check` | Parses only and prints status |
| `--filter-module` | Imports Python module |

---

## Error Output Contract

Engine errors include:
- error type
- line
- column
- message
- optional source excerpt
- caret pointer

Example shape:
```text
ParseError at line 3, column 1: unexpected {% endif %}
  > {% endif %}
    ^
```

---

*Constitution reference: Article 4 (input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Mini Template Engine
**Template Rendering Group | Document 4 of 5**

---

## Requirements

### Runtime

- Python 3.10 or newer
- No runtime dependencies

### Development

- pytest
- coverage
- hypothesis
- ruff
- mypy
- pre-commit
- build
- twine

---

## Installation

### Editable install

```bash
pip install -e .
```

### Editable install with dev tools

```bash
pip install -e ".[dev]"
```

---

## Basic Smoke Test

```bash
python -m template_engine examples/hello.tmpl --context examples/context.json
```

Expected:
- rendered output printed to stdout

---

## CLI Health Checks

### Help

```bash
template-engine --help
```

---

### Version

```bash
template-engine --version
```

---

### Syntax check

```bash
template-engine examples/conditions.tmpl --check
```

Expected:
```text
ok
```

---

### Token dump

```bash
template-engine examples/invoice.tmpl --dump-tokens
```

Expected:
- token list with token type, line, column, trim flags, and value

---

### AST dump

```bash
template-engine examples/invoice.tmpl --dump-ast
```

Expected:
- human-readable AST tree

---

### Render with inline context

```bash
template-engine examples/hello.tmpl --set user.name=Princeton
```

---

## Library Health Check

```python
from template_engine import Template

output = Template("Hello, {{ name | title }}!").render({"name": "princeton"})
assert output == "Hello, Princeton!"
```

---

## Running Tests

```bash
pytest
```

Coverage gate:

```bash
coverage run -m pytest -q
coverage report --fail-under=95
```

---

## Running Quality Checks

```bash
ruff check template_engine tests
ruff format --check template_engine tests
mypy template_engine
```

---

## CI Parity

The CI workflow runs:
- Ubuntu and Windows
- Python 3.10, 3.11, 3.12, 3.13, 3.14
- install with dev extras and constraints
- Ruff lint
- Ruff format check
- mypy
- pytest through coverage
- coverage report with fail-under 95

---

## Standard Operating Procedures

### Render a template with a JSON context

```bash
template-engine template.tmpl --context context.json
```

---

### Render to a file

```bash
template-engine template.tmpl --context context.json --output output.html
```

---

### Check syntax before render

```bash
template-engine template.tmpl --check
```

---

### Debug lexer output

```bash
template-engine template.tmpl --dump-tokens --include-comments
```

---

### Debug parser output

```bash
template-engine template.tmpl --dump-ast
```

---

### Use strict mode

```bash
template-engine template.tmpl --context context.json --strict
```

Use strict mode when missing variables should fail fast instead of rendering as empty strings.

---

### Disable escaping for non-HTML output

```bash
template-engine template.txt --context context.json --no-autoescape
```

---

### Keep escaping on for HTML

Default behavior is safer:

```bash
template-engine page.html.tmpl --context context.json
```

Use `| safe` only for trusted HTML.

---

### Add custom filters

Create a module exposing `filter_registry`, then run:

```bash
template-engine template.tmpl --filter-module my_filters
```

or:

```bash
template-engine template.tmpl --filter-module my_filters:registry
```

---

## Expected Failure Modes

### Unterminated tag

Cause:
```jinja
Hello {{ name
```

Expected:
- `LexerError`
- exit code `1` in CLI

Resolution:
- close the tag with `}}`

---

### Unexpected end tag

Cause:
```jinja
{% endif %}
```

Expected:
- `ParseError`
- exit code `1`

Resolution:
- remove the tag or add matching `{% if %}`

---

### Unsupported condition

Cause:
```jinja
{% if a and b %}
```

Expected:
- `ParseError`
- message explains `and`/`or` are not supported

Resolution:
- use nested `{% if %}` blocks

---

### Missing variable in strict mode

Cause:
```bash
template-engine template.tmpl --strict
```

Expected:
- `RenderError`
- exit code `1`

Resolution:
- add the variable to context
- use `default`
- remove strict mode where empty rendering is acceptable

---

### Private attribute access

Cause:
```jinja
{{ user._password }}
```

Expected:
- `RenderError`

Resolution:
- expose only safe public data in context

---

### Callable or property access

Cause:
```jinja
{{ user.delete }}
{{ user.expensive_property }}
```

Expected:
- `RenderError`

Resolution:
- precompute safe values before passing context to the template

---

### Unknown filter

Cause:
```jinja
{{ name | unknown }}
```

Expected:
- `RenderError`

Resolution:
- register the filter
- correct the filter name

---

### Invalid JSON context

Cause:
```bash
template-engine template.tmpl --context bad.json
```

Expected:
- exit code `2`

Resolution:
- fix JSON
- ensure root value is an object

---

### Invalid `--set`

Cause:
```bash
template-engine template.tmpl --set user-name=Princeton
```

Expected:
- exit code `2`

Resolution:
- use dotted identifiers such as `user.name=Princeton`

---

## Troubleshooting Decision Tree

```text
Command failed
  |
  +-- exit 1?
  |     |
  |     +-- LexerError -> check tag delimiters and raw blocks
  |     +-- ParseError -> check block nesting and expression grammar
  |     +-- RenderError -> check context variables, filters, strict mode, private/callable access
  |
  +-- exit 2?
  |     |
  |     +-- Check template file path
  |     +-- Check context JSON
  |     +-- Check --set syntax
  |     +-- Check --filter-module import path
  |
  +-- exit 3?
        |
        +-- unexpected internal error; reduce template to reproduction and run tests
```

---

## Recovery Procedures

### Recover from syntax error

1. Run `--dump-tokens` to see tokenization.
2. Run `--dump-ast` after fixing token-level issues.
3. Check matching `{% if %}` / `{% endif %}` and `{% for %}` / `{% endfor %}` pairs.

---

### Recover from unsafe output

1. Keep autoescape enabled.
2. Remove unnecessary `| safe`.
3. Pass plain data, not already-rendered HTML, where possible.
4. Use `escape` explicitly when transforming trusted/unsafe mixed values.

---

### Recover from missing variables

1. Run in strict mode to identify missing path.
2. Add the key to context.
3. Use `default` where missing values are valid.
4. Avoid hiding real data bugs with broad defaults.

---

### Recover from custom filter failure

1. Confirm module imports.
2. Confirm attribute resolves to `FilterRegistry`.
3. Confirm filter name is an identifier and does not start with `_`.
4. Raise `RenderError` directly for expected filter errors.

---

## Maintenance Notes

- Keep the expression grammar small unless a new ADR expands it.
- Do not introduce `eval`.
- Do not allow method calls or property access.
- Preserve autoescaping default.
- Add tests for every new syntax form.
- Keep `Template` as the public facade.
- Keep CLI debug modes aligned with lexer/parser internals.
- Preserve line/column error reporting.
- Re-run Ruff, mypy, pytest, and coverage before release.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Mini Template Engine
**Template Rendering Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because the goal was to build a real language tool, not just a string replacement helper. A mini template engine touches several fundamental areas: lexical analysis, parsing, AST design, scoped runtime evaluation, escaping policy, error reporting, and CLI ergonomics.

The staged architecture keeps those concerns separate. The lexer knows about delimiters and whitespace trimming. The parser knows about grammar and block structure. The renderer knows about runtime values and output. The context stack knows about safe lookup. Filters provide controlled extensibility. The CLI exposes the pipeline for debugging.

That separation makes the project portfolio-ready because it demonstrates both implementation skill and architectural restraint.

---

## What Was Intentionally Omitted

**Full Jinja compatibility:** This is a learning engine, not a production replacement.

**`eval` and arbitrary Python:** Omitted for safety and clarity.

**Method calls and property access:** Omitted to prevent templates from executing application behavior.

**Includes/macros/inheritance:** Omitted to keep V1 single-file and avoid loader/path complexity.

**`and` / `or`:** Omitted to keep the condition grammar small.

**Async rendering:** Out of scope.

**Context-aware HTML escaping:** Autoescape is useful, but not a complete browser-context sanitizer.

**Streaming rendering:** The renderer returns one complete string.

---

## Biggest Weakness

The biggest weakness is that escaping is HTML escaping, not full context-aware escaping. Rendering into HTML text content is safer by default, but rendering inside JavaScript, CSS, URLs, or attributes can require different escaping rules. This is acceptable for the stated scope, but it must be documented honestly.

The second weakness is performance on large loop-heavy templates. The renderer materializes loop iterables into lists so it can provide `loop.length` and `loop.last`. That is convenient but not streaming-friendly.

The third weakness is limited expression power. This is a design strength for safety, but users familiar with Jinja may expect `and`, `or`, arithmetic, includes, or macros.

---

## Scaling Considerations

**If syntax grows:**
- keep the grammar documented
- add AST nodes deliberately
- add tests for every new branch
- avoid adding arbitrary Python evaluation

**If performance becomes important:**
- consider bytecode or compiled render plans
- add template caching across files
- benchmark before optimizing
- avoid breaking the current public API

**If templates become multi-file:**
- define a loader interface
- constrain paths
- prevent recursion loops
- add cache invalidation
- add include/inheritance ADRs

**If HTML security scope expands:**
- add context-aware escaping
- document attribute/URL/script/style handling
- consider safer HTML rendering conventions

---

## What the Next Refactor Would Be

1. **Formal grammar tests** — mirror the documented grammar with test cases for every syntax production.

2. **Better AST serialization** — provide a machine-readable debug format in addition to human dumps.

3. **Loader interface** — only after documenting path/security rules.

4. **Streaming renderer option** — useful for large output, but would require loop metadata trade-offs.

5. **Context-aware escaping** — the most important security upgrade for HTML-heavy use.

---

## What This Project Taught

- **A template engine is a language runtime.** Even a small syntax needs tokens, grammar, AST, evaluation, errors, and tests.

- **Security is architectural.** Avoiding `eval` is not enough; lookup rules, autoescaping, and filters must all be constrained.

- **Line/column errors matter.** They turn parser failures from confusing messages into actionable feedback.

- **Debug modes are powerful.** Token and AST dumps make the internals visible to users and reviewers.

- **Scope discipline creates quality.** Single-file templates, small expressions, and tree walking make the engine complete enough without pretending to be Jinja.

- **Tests are the contract.** Lexer behavior, parser nesting, rendering semantics, escaping, filters, CLI exits, and debug output should all be locked down.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Mini Template Engine.*
