# ADR 0005: Single-File Templates Only

## Decision

Version 1 supports only single-file templates. There is no `include`, `extends`,
macro, or import mechanism.

## Reason

Composition features require a loader, dependency graph, and partial caching.
The academic goal is to keep the lexer, parser, AST, and renderer easy to read
and test in one repository without framework scaffolding.

## Trade-Off

Callers compose templates in Python by concatenating source strings, rendering
partials separately, or building context before a single render call.
