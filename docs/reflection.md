# Project Reflection

## Goal

Build a readable, testable template engine that demonstrates compiler pipeline
fundamentals without relying on frameworks or `eval`.

## What went well

- **Clear stage boundaries** — each module has one job, which made debugging and
  grading straightforward.
- **Security defaults** — autoescaping and rejecting callables/private names are
  simple rules with high impact.
- **ADRs** — documenting trade-offs (tree walk vs bytecode, no includes) shows
  intentional design rather than accidental limitations.

## Challenges

- **Expression grammar minimalism** — balancing Jinja familiarity with a small
  parser led to edge cases (literal keywords vs paths, `strict` vs `default`).
- **Error ergonomics** — line/column tracking across lex, parse, and render
  required consistent metadata on AST nodes.
- **Scope semantics** — loop and `set` blocks needed explicit stack behavior to
  avoid mutating caller context.

## Trade-offs accepted

- Tree-walking interpreter over bytecode (clarity over speed)
- Single-file templates only (no loader graph)
- Python truthiness for conditions (not Jinja-style undefined objects)

## If I continued to v2

1. Template loader with cache and partial composition
2. Richer conditions (`and` / `or`) via AST instead of regex splitting
3. Compiled render functions for hot paths
4. Structured error recovery suggestions in CLI output

## Learning outcomes demonstrated

- Finite-state scanning and token emission
- Recursive descent parsing with stop tags
- AST design with frozen dataclasses
- Contextual evaluation with lexical scoping
- Secure-by-default output encoding
