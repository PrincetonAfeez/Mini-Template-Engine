#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ruff lint =="
ruff check template_engine tests

echo "== ruff format check =="
ruff format --check template_engine tests

echo "== mypy =="
mypy template_engine

echo "== tests + coverage =="
coverage run -m pytest -q
coverage report --fail-under=95

echo "All checks passed."
