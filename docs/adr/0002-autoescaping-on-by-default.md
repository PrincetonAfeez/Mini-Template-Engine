# ADR 0002: Autoescaping On By Default

## Decision

Escape variable output by default.

## Reason

Template engines often render HTML. Secure defaults are better than requiring
callers to remember to opt in.

## Trade-Off

Plain-text templates may not want escaping, so the library supports
`autoescape=False` and the CLI supports `--no-autoescape`.
