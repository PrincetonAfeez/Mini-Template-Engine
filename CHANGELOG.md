# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Lexer, parser, AST, and tree-walking renderer pipeline
- Variables, filters, conditionals, loops, raw blocks, comments, whitespace trim
- `{% set %}` assignment blocks and numeric list index access (`items.0`)
- Keyword literals (`true`, `false`, `none`, `null`) in output expressions
- Variable-to-variable condition comparisons and variable filter arguments
- `default_if_none` filter; `default` filter works with `strict=True`
- HTML autoescaping on by default with `safe` and `escape` filters
- CLI with `--check`, `--dump-tokens`, `--dump-ast`, `--filter-module`, `--version`, `-v`
- Source line excerpts in CLI template errors
- Architecture Decision Records (ADRs 0001–0005)
- Example templates, integration tests, CI, and developer tooling

[Unreleased]: https://github.com/PrincetonAfeez/Mini-Template-Engine/compare/main...HEAD
