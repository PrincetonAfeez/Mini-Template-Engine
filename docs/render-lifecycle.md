# Render Lifecycle

How a template moves from source text to output.

```mermaid
sequenceDiagram
    participant User
    participant Template
    participant Lexer
    participant Parser
    participant Renderer
    participant Context

    User->>Template: render(context)
    Template->>Lexer: lex(source)
    Lexer-->>Template: tokens
    Template->>Parser: parse(tokens)
    Parser-->>Template: AST
    Template->>Renderer: render(ast, context)
    Renderer->>Context: push root scope
    loop each AST node
        alt TextNode / RawNode
            Renderer-->>Renderer: append literal text
        else VariableNode
            Renderer->>Context: resolve expression
            Renderer-->>Renderer: stringify + autoescape
        else SetNode
            Renderer->>Context: assign name in current scope
        else IfNode
            Renderer->>Context: evaluate condition
            Renderer-->>Renderer: render chosen branch
        else ForNode
            Renderer->>Context: evaluate iterable
            loop each item
                Renderer->>Context: push loop scope
                Renderer-->>Renderer: render body
                Renderer->>Context: pop loop scope
            end
        end
    end
    Renderer-->>User: output string
```

## Scope rules

| Event | Scope behavior |
|-------|----------------|
| `render()` starts | Root context dict becomes bottom scope |
| `{% for %}` iteration | Push `{ item, loop }`; pop after body |
| `{% set %}` | Assigns into innermost scope (can shadow outers) |
| Variable lookup | Search scopes inner → outer |

## Filter evaluation

1. Evaluate expression base (lenient when `strict` + `default` filter).
2. Evaluate filter arguments left to right.
3. Apply each filter in chain order.
4. Apply autoescaping when stringifying variable output (unless `SafeString`).

## Complexity

| Stage | Time | Space |
|-------|------|-------|
| Lex | O(n) | O(n) tokens |
| Parse | O(n) | O(n) AST nodes |
| Render | O(nodes × context depth) | O(scope depth + loop items materialized) |

See [ADR 0001](adr/0001-tree-walking-interpreter.md) for the performance trade-off.
