# ADR 0004: Library Core Over Framework-First Design

## Decision

Build a reusable Python library first. Keep CLI and any future web layer as
adapters.

## Reason

The engine should be testable without a framework and should have one clear
implementation of lexing, parsing, rendering, filters, and context lookup.

## Trade-Off

A web showcase waits until the engine and CLI are complete.
