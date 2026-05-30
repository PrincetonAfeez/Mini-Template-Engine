# Contributing

Thanks for your interest in Mini Template Engine.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e ".[dev]"
pre-commit install
```

## Quality checks

```bash
# Windows
.\scripts\test.ps1

# macOS/Linux
./scripts/test.sh
```

The script runs Ruff, Mypy, pytest, and coverage (95% minimum on `template_engine/`).

Run tests directly:

```bash
pytest
coverage run -m pytest -q && coverage report --fail-under=95
```

## Pull requests

1. Fork the repository and create a feature branch.
2. Add or update tests for behavior changes.
3. Update `CHANGELOG.md` under **Unreleased** when appropriate.
4. Ensure `ruff check`, `mypy template_engine`, and `coverage report --fail-under=95` pass.
5. Open a PR with a clear description and test plan.

## Architecture changes

Significant design changes should include a new ADR in `docs/adr/`.

## Code style

- Standard library only for runtime dependencies
- Match existing module boundaries: lexer → parser → renderer
- Prefer explicit error types (`LexerError`, `ParseError`, `RenderError`)
