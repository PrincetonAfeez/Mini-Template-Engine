# Mini Template Engine

A pure Python template engine built as a small compiler-style pipeline:

1. Lex source text into tokens.
2. Parse tokens into an AST.
3. Render by recursively walking the AST with a context.

Runtime code uses only the Python standard library.

## Library Usage

```python
from template_engine import Template

template = Template("Hello, {{ user.name | title }}!")
output = template.render({"user": {"name": "princeton"}})

print(output)
# Hello, Princeton!
```

Autoescaping is enabled by default:

```python
Template("{{ value }}").render({"value": "<b>x</b>"})
# "&lt;b&gt;x&lt;/b&gt;"
```

Use `safe` only for trusted values:

```python
Template("{{ value | safe }}").render({"value": "<b>x</b>"})
# "<b>x</b>"
```

## CLI Usage

Render a file:

```bash
python -m template_engine examples/hello.tmpl --context examples/context.json
```

Render from stdin:

```bash
type examples/hello.tmpl | python -m template_engine - --context examples/context.json
```

Check syntax:

```bash
python -m template_engine examples/conditions.tmpl --check
```

Dump tokens or AST:

```bash
python -m template_engine examples/loop.tmpl --dump-tokens
python -m template_engine examples/loop.tmpl --dump-ast
```

Inline context values:

```bash
python -m template_engine examples/hello.tmpl --set user.name=Princeton
```

## Supported Syntax

Variables:

```jinja
{{ name }}
{{ user.name }}
```

Filters:

```jinja
{{ name | trim | title }}
{{ price | round(2) }}
{{ items | join(", ") }}
{{ missing | default("N/A") }}
```

Conditionals:

```jinja
{% if user.is_admin %}
Admin
{% elif user.is_staff %}
Staff
{% else %}
User
{% endif %}
```

Loops:

```jinja
{% for user in users %}
{{ loop.index }}. {{ user.name }}
{% endfor %}
```

Raw blocks:

```jinja
{% raw %}
This is literal: {{ name }}
{% endraw %}
```

Comments:

```jinja
{# ignored #}
```

Whitespace trimming is supported with dash markers:

```jinja
Hello {{- name -}} !
```

## Deliberate Limits

- No `eval`.
- No arbitrary Python expressions.
- No method calls from templates.
- No private attribute access.
- No includes, inheritance, macros, async rendering, bytecode, or Django layer.

## Tests

```bash
python -m unittest discover
```
