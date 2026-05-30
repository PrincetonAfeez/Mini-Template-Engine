"""Pytest coverage for the public package API."""

from __future__ import annotations

import template_engine
from template_engine import (
    FilterRegistry,
    ForNode,
    IfNode,
    LexerError,
    ParseError,
    RenderError,
    SetNode,
    Template,
    TemplateEngineError,
    TemplateNode,
    TextNode,
    VariableNode,
    __version__,
    default_filter_registry,
    format_error,
)


def test_version_is_string():
    assert isinstance(__version__, str)
    assert __version__ == template_engine.__version__


def test_all_exports_importable():
    exported = set(template_engine.__all__)
    assert exported == {
        "ASTNode",
        "FilterRegistry",
        "ForNode",
        "IfNode",
        "LexerError",
        "ParseError",
        "RenderError",
        "SafeString",
        "SetNode",
        "Template",
        "TemplateEngineError",
        "TemplateNode",
        "TextNode",
        "VariableNode",
        "__version__",
        "default_filter_registry",
        "format_error",
    }


def test_error_hierarchy():
    assert issubclass(LexerError, TemplateEngineError)
    assert issubclass(ParseError, TemplateEngineError)
    assert issubclass(RenderError, TemplateEngineError)


def test_default_filter_registry_returns_registry():
    registry = default_filter_registry()
    assert isinstance(registry, FilterRegistry)
    assert registry.all_filters()


def test_template_instantiation():
    tmpl = Template("{{ x }}")
    assert tmpl.source == "{{ x }}"
    assert tmpl.strict is False
    assert tmpl.autoescape is True


def test_format_error_without_source():
    err = ParseError("bad syntax", line=2, column=5)
    assert "line 2" in format_error(err)
    assert "bad syntax" in format_error(err)


def test_node_types_are_dataclasses():
    assert TextNode.__dataclass_fields__
    assert VariableNode.__dataclass_fields__
    assert ForNode.__dataclass_fields__
    assert IfNode.__dataclass_fields__
    assert SetNode.__dataclass_fields__
    assert TemplateNode.__dataclass_fields__
