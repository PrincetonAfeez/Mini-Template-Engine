# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Threat model

Mini Template Engine renders untrusted template text with caller-supplied context data.
It is designed for educational and portfolio use, not as a full replacement for
production template systems without review.

### Mitigations

- **No arbitrary Python execution** — templates cannot call functions, methods, or `eval`.
  Property and other descriptor getters are not invoked during attribute lookup; only
  plain instance attributes, class data attributes, mappings, and sequences are read.
- **No private attribute access** — names starting with `_` are rejected.
- **HTML autoescaping on by default** — variable output is escaped unless marked `safe`.
- **Callable rejection** — context values that resolve to callables raise `RenderError`.
- **Trusted context** — prefer plain dictionaries (and similar mappings) when rendering
  untrusted templates; object context is intended for simple data carriers you control.

### Known limitations

- Autoescaping targets HTML. Plain-text or other output formats may require
  `autoescape=False` or custom filters.
- Pre-escaped HTML in context is double-escaped unless passed through `| safe`
  (only for trusted values).
- There is no sandbox for CPU or memory use; pathological templates can consume
  resources proportional to input size.

## Reporting a vulnerability

Please report security issues privately via GitHub Security Advisories:

https://github.com/PrincetonAfeez/Mini-Template-Engine/security/advisories/new

Do not open public issues for undisclosed vulnerabilities.
