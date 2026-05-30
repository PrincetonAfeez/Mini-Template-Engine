# ADR 0001: Tree-Walking Interpreter Over Compile-To-Python

## Decision

Render templates by recursively walking the parsed AST.

## Reason

The project is meant to teach lexing, parsing, AST design, and recursive
evaluation. A tree-walking renderer keeps each stage visible and easy to test.

## Trade-Off

It is slower than compiling templates to Python or bytecode, but performance is
not a version 1 goal.
