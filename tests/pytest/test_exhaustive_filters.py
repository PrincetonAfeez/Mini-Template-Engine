"""Exhaustive pytest tests for template_engine.filters."""

from __future__ import annotations

import pytest

from template_engine.context import MISSING
from template_engine.errors import RenderError
from template_engine.escape import SafeString
from template_engine.filters import FilterRegistry, default_filter_registry


class TestFilterRegistry:
    def test_register_and_get(self):
        registry = FilterRegistry()
        registry.register("double", lambda v: v * 2)
        assert registry.get("double")(5) == 10

    def test_register_invalid_names(self):
        registry = FilterRegistry()
        with pytest.raises(ValueError):
            registry.register("9bad", lambda v: v)
        with pytest.raises(ValueError):
            registry.register("_hidden", lambda v: v)

    def test_unknown_filter(self):
        registry = FilterRegistry()
        with pytest.raises(RenderError, match="unknown filter"):
            registry.apply("missing", "x")

    def test_filter_exception_wrapped(self):
        registry = FilterRegistry()

        def boom(_value):
            raise RuntimeError("fail")

        registry.register("boom", boom)
        with pytest.raises(RenderError, match="filter 'boom' failed"):
            registry.apply("boom", "x")

    def test_render_error_passthrough(self):
        registry = FilterRegistry()
        registry.register("bad", lambda _v: (_ for _ in ()).throw(RenderError("inner")))
        with pytest.raises(RenderError, match="inner"):
            registry.apply("bad", "x")

    def test_extend_overwrites(self):
        a = FilterRegistry()
        b = FilterRegistry()
        a.register("x", lambda v: "a")
        b.register("x", lambda v: "b")
        a.extend(b)
        assert a.apply("x", None) == "b"

    def test_all_filters_copy(self):
        registry = default_filter_registry()
        copy = registry.all_filters()
        copy["upper"] = lambda v: "hacked"
        assert registry.apply("upper", "hi") == "HI"

    def test_items_returns_registered_pairs(self):
        registry = FilterRegistry()
        registry.register("double", lambda v: v * 2)
        pairs = dict(registry.items())
        assert pairs["double"](5) == 10
        assert "double" in registry.all_filters()


class TestBuiltinFilters:
    @pytest.fixture
    def reg(self):
        return default_filter_registry()

    @pytest.mark.parametrize(
        ("name", "value", "args", "expected"),
        [
            ("upper", "hi", (), "HI"),
            ("lower", "HI", (), "hi"),
            ("title", "hello world", (), "Hello World"),
            ("trim", "  x  ", (), "x"),
            ("default", MISSING, ("fallback",), "fallback"),
            ("default", None, ("fb",), "fb"),
            ("default", "", ("fb",), "fb"),
            ("default", "keep", ("fb",), "keep"),
            ("default_if_none", None, ("fb",), "fb"),
            ("default_if_none", "", ("fb",), ""),
            ("length", [1, 2, 3], (), 3),
            ("length", None, (), 0),
            ("length", MISSING, (), 0),
            ("join", ["a", "b"], (",",), "a,b"),
            ("join", None, (), ""),
            ("join", MISSING, (), ""),
            ("round", 1.234, (2,), 1.23),
            ("round", None, (), ""),
            ("round", MISSING, (), ""),
        ],
    )
    def test_builtin_filters(self, reg, name, value, args, expected):
        assert reg.apply(name, value, *args) == expected

    def test_upper_with_missing(self, reg):
        assert reg.apply("upper", MISSING) == ""

    def test_lower_with_missing(self, reg):
        assert reg.apply("lower", MISSING) == ""

    def test_escape_filter(self, reg):
        result = reg.apply("escape", "<b>")
        assert isinstance(result, SafeString)
        assert result == "&lt;b&gt;"

    def test_safe_filter(self, reg):
        result = reg.apply("safe", "<b>")
        assert isinstance(result, SafeString)
        assert result == "<b>"

    @pytest.mark.parametrize(
        ("value", "message"),
        [
            ("abc", "not a string"),
            (123, "expected an iterable"),
        ],
    )
    def test_join_errors(self, reg, value, message):
        with pytest.raises(RenderError, match=message):
            reg.apply("join", value)
