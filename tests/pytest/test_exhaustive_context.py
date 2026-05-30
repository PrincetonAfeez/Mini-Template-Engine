"""Exhaustive pytest tests for template_engine.context."""

from __future__ import annotations

import pytest

from template_engine.context import MISSING, ContextStack, LoopHelper
from template_engine.errors import RenderError


class TestLoopHelper:
    def test_fields(self):
        helper = LoopHelper(index=1, index0=0, first=True, last=False, length=3)
        assert helper.index == 1
        assert helper.first is True


class TestContextStack:
    def test_resolve_simple(self):
        stack = ContextStack({"name": "Ada"})
        assert stack.resolve(("name",)) == "Ada"

    def test_resolve_nested_mapping(self):
        stack = ContextStack({"user": {"name": "Ada"}})
        assert stack.resolve(("user", "name")) == "Ada"

    def test_resolve_sequence_index(self):
        stack = ContextStack({"items": ["a", "b"]})
        assert stack.resolve(("items", "0")) == "a"
        assert stack.resolve(("items", "1")) == "b"

    def test_resolve_attribute(self):
        obj = type("Obj", (), {"title": "T"})()
        stack = ContextStack({"obj": obj})
        assert stack.resolve(("obj", "title")) == "T"

    def test_resolve_missing_lenient(self):
        stack = ContextStack({})
        assert stack.resolve(("missing",)) is MISSING

    def test_resolve_missing_strict(self):
        stack = ContextStack({}, strict=True)
        with pytest.raises(RenderError, match="missing variable"):
            stack.resolve(("missing",))

    def test_resolve_empty_path(self):
        stack = ContextStack({})
        assert stack.resolve(()) is MISSING

    def test_resolve_missing_intermediate(self):
        stack = ContextStack({})
        assert stack.resolve(("missing", "child")) is MISSING

    def test_resolve_index_out_of_range(self):
        stack = ContextStack({"items": []})
        assert stack.resolve(("items", "0")) is MISSING

    def test_private_name_rejected(self):
        stack = ContextStack({"_secret": 1})
        with pytest.raises(RenderError, match="private"):
            stack.resolve(("_secret",))

    def test_private_part_rejected(self):
        stack = ContextStack({"user": {"name": "x"}})
        with pytest.raises(RenderError, match="private"):
            stack.resolve(("user", "_secret"))

    def test_callable_root_rejected(self):
        stack = ContextStack({"fn": lambda: 1})
        with pytest.raises(RenderError, match="callable"):
            stack.resolve(("fn",))

    def test_callable_mapping_value_rejected(self):
        stack = ContextStack({"data": {"fn": lambda: 1}})
        with pytest.raises(RenderError, match="callable"):
            stack.resolve(("data", "fn"))

    def test_callable_sequence_item_rejected(self):
        stack = ContextStack({"items": [lambda: 1]})
        with pytest.raises(RenderError, match="callable"):
            stack.resolve(("items", "0"))

    def test_callable_attribute_rejected(self):
        obj = type("Obj", (), {})()
        obj.method = lambda: 1
        stack = ContextStack({"obj": obj})
        with pytest.raises(RenderError, match="callable"):
            stack.resolve(("obj", "method"))

    def test_resolve_resolution_error_wrapped(self):
        class BadAttr:
            @property
            def boom(self):
                raise TypeError("boom")

        stack = ContextStack({"obj": BadAttr()})
        with pytest.raises(RenderError, match="could not be resolved"):
            stack.resolve(("obj", "boom"))

    def test_push_pop_scopes(self):
        stack = ContextStack({"outer": 1})
        stack.push({"inner": 2})
        assert stack.resolve(("inner",)) == 2
        assert stack.resolve(("outer",)) == 1
        stack.pop()
        with pytest.raises(RenderError, match="cannot pop root"):
            stack.pop()

    def test_assign(self):
        stack = ContextStack({})
        stack.assign("x", 42)
        assert stack.resolve(("x",)) == 42

    def test_assign_private_rejected(self):
        stack = ContextStack({})
        with pytest.raises(RenderError):
            stack.assign("_x", 1)

    def test_lenient_missing_with_strict(self):
        stack = ContextStack({}, strict=True)
        assert stack.resolve(("missing",), lenient=True) is MISSING
