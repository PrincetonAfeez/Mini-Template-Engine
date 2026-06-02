# Schema Folder — Mini Template Engine

This folder contains simple JSON Schema files for the repository's main contracts. They are intentionally lightweight and documentation-friendly; they do not replace the engine's real parser, renderer, or test suite.

## Files

| File | Purpose |
| --- | --- |
| `context.schema.json` | Validates the top-level JSON context object accepted by `Template.render(context)` and `--context`. |
| `template-source.schema.json` | Validates a metadata wrapper around a template source string. Full template grammar should still be checked with `Template.check()` or `template-engine --check`. |
| `token.schema.json` | Documents lexer token records: `TEXT`, `VARIABLE`, `BLOCK`, `RAW`, `COMMENT`, and `EOF`. |
| `ast.schema.json` | Documents a portable JSON representation of the AST dataclasses: `TemplateNode`, `TextNode`, `VariableNode`, `RawNode`, `IfNode`, `ForNode`, and `SetNode`. |
| `filter-registry.schema.json` | Documents filter registry metadata for built-in or custom filters. |
| `cli-options.schema.json` | Documents a JSON representation of supported CLI options. |

## Notes

- These files are for documentation, portfolio review, tooling experiments, and validation of JSON-shaped inputs/outputs.
- The engine itself is pure Python and does not require these schema files at runtime.
- No GitHub write actions were performed to create this folder.
