"""Shared pytest fixtures for the mini template engine test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from template_engine.filters import FilterRegistry, default_filter_registry
from template_engine.template import Template


@pytest.fixture
def registry() -> FilterRegistry:
    return default_filter_registry()


@pytest.fixture
def empty_template() -> Template:
    return Template("")


@pytest.fixture
def hello_template() -> Template:
    return Template("Hello {{ name | title }}!")


@pytest.fixture
def examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def invoice_context(examples_dir: Path) -> dict:
    return json.loads((examples_dir / "context.json").read_text(encoding="utf-8"))


@pytest.fixture
def tmp_template_file(tmp_path: Path):
    def _write(source: str, name: str = "test.tmpl") -> Path:
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def tmp_context_file(tmp_path: Path):
    def _write(context: dict, name: str = "ctx.json") -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(context), encoding="utf-8")
        return path

    return _write
