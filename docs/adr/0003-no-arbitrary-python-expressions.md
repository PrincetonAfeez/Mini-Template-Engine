# ADR 0003: No Arbitrary Python Expressions

## Decision

Support a small expression grammar: dotted lookups, literals, filter chains, and
simple conditions.

## Reason

Evaluating arbitrary template-supplied Python creates a code execution surface
and turns the project into a much larger language implementation.

## Trade-Off

The language is intentionally less expressive than Python or Jinja. Complex
logic should live in calling code.
