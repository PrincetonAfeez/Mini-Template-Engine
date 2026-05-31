"""Exhaustive pytest tests for template_engine.cli."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import pytest

from template_engine.cli import (
    _apply_assignment,
    _build_parser,
    _load_filter_registry,
    _print_stats,
    _read_context,
    _read_template,
    main,
)
from template_engine.filters import FilterRegistry
from template_engine.template import Template


@pytest.mark.cli
class TestBuildParser:
    def test_parser_has_expected_args(self):
        parser = _build_parser()
        assert parser.parse_args(["--version"]).version is True
        assert parser.parse_args(["--check"]).check is True


@pytest.mark.cli
class TestReadTemplate:
    def test_read_from_file(self, tmp_template_file):
        path = tmp_template_file("{{ x }}", "tmpl.tmpl")
        assert _read_template(str(path)) == "{{ x }}"

    def test_read_from_stdin(self):
        with patch("template_engine.cli.sys.stdin", io.StringIO("stdin content")):
            assert _read_template("-") == "stdin content"


@pytest.mark.cli
class TestReadContext:
    def test_empty_context(self):
        assert _read_context(None) == {}

    def test_valid_context_file(self, tmp_context_file):
        path = tmp_context_file({"name": "Ada"})
        assert _read_context(str(path)) == {"name": "Ada"}

    def test_context_not_object(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text(json.dumps([1, 2]), encoding="utf-8")
        with pytest.raises(ValueError, match="object"):
            _read_context(str(path))


@pytest.mark.cli
class TestApplyAssignment:
    def test_simple_assignment(self):
        ctx: dict = {}
        _apply_assignment(ctx, "name=Ada")
        assert ctx["name"] == "Ada"

    def test_literal_assignment(self):
        ctx: dict = {}
        _apply_assignment(ctx, "count=42")
        assert ctx["count"] == 42
        assert isinstance(ctx["count"], int)

    def test_literal_assignment_keeps_bool_and_none(self):
        ctx: dict = {}
        _apply_assignment(ctx, "flag=true")
        _apply_assignment(ctx, "blank=none")
        assert ctx["flag"] is True
        assert ctx["blank"] is None

    def test_later_set_overwrites_earlier_nested_dict(self):
        # Pinning current behavior: a later --set with a shorter key path
        # clobbers any deeper structure built up by previous --set values.
        # Documented in the CLI help; this test guards against silent change.
        ctx: dict = {}
        _apply_assignment(ctx, "a.b=1")
        _apply_assignment(ctx, "a=2")
        assert ctx["a"] == 2

    def test_later_set_overwrites_earlier_scalar(self):
        ctx: dict = {}
        _apply_assignment(ctx, "name=first")
        _apply_assignment(ctx, "name=second")
        assert ctx["name"] == "second"

    def test_nested_assignment(self):
        ctx: dict = {}
        _apply_assignment(ctx, "user.name=Ada")
        assert ctx["user"]["name"] == "Ada"

    def test_non_literal_fallback(self):
        ctx: dict = {}
        _apply_assignment(ctx, "msg=hello world")
        assert ctx["msg"] == "hello world"

    @pytest.mark.parametrize(
        "assignment",
        [
            "bad",
            "=value",
            "a..b=1",
            "a.=1",
            "user.name=1",
            "9bad=1",
            "user name=x",
            "user.9bad=1",
        ],
    )
    def test_invalid_assignments(self, assignment):
        ctx: dict = {"user": "not-a-dict"} if assignment == "user.name=1" else {}
        with pytest.raises(ValueError):
            _apply_assignment(ctx, assignment)


@pytest.mark.cli
class TestLoadFilterRegistry:
    def test_load_from_tests_support(self):
        registry = _load_filter_registry("tests.support.custom_filters")
        assert isinstance(registry, FilterRegistry)

    def test_load_with_attribute(self):
        registry = _load_filter_registry("tests.support.custom_filters:filter_registry")
        assert isinstance(registry, FilterRegistry)

    def test_module_not_found(self):
        with pytest.raises(ModuleNotFoundError):
            _load_filter_registry("no_such_module_xyz")

    def test_missing_attribute(self):
        with pytest.raises(AttributeError):
            _load_filter_registry("json:not_a_registry")

    def test_not_a_registry(self):
        with pytest.raises(ValueError, match="FilterRegistry"):
            _load_filter_registry("json:loads")


@pytest.mark.cli
class TestPrintStats:
    def test_print_stats_logs_diagnostics(self, caplog):
        import logging

        template = Template("{{ x }}")
        with caplog.at_level(logging.INFO, logger="template_engine.cli"):
            _print_stats(template, 0.0, rendered=5)
        assert "tokens=" in caplog.text
        assert "output_chars=5" in caplog.text


@pytest.mark.cli
class TestMain:
    def test_version(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--version"])
        assert code == 0
        assert out.getvalue().strip()

    def test_render_stdout(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="Hello {{ name }}!"):
            with redirect_stdout(out):
                code = main(["-", "--set", "name=World"])
        assert code == 0
        assert out.getvalue() == "Hello World!"

    def test_render_to_file(self, tmp_path):
        output = tmp_path / "out.html"
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            code = main(["-", "--set", "x=ok", "-o", str(output)])
        assert code == 0
        assert output.read_text(encoding="utf-8") == "ok"

    def test_read_template_from_path(self, tmp_template_file):
        path = tmp_template_file("{{ x }}")
        out = io.StringIO()
        with redirect_stdout(out):
            code = main([str(path), "--set", "x=1"])
        assert code == 0
        assert out.getvalue() == "1"

    def test_check_mode(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ ok }}"):
            with redirect_stdout(out):
                code = main(["-", "--check"])
        assert code == 0
        assert "ok" in out.getvalue()

    def test_check_verbose(self):
        err = io.StringIO()
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ ok }}"):
            with redirect_stderr(err):
                with redirect_stdout(out):
                    code = main(["-", "--check", "-v"])
        assert code == 0
        assert "top_level_nodes=" in err.getvalue()

    def test_dump_tokens(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--dump-tokens"])
        assert code == 0
        assert "VARIABLE" in out.getvalue()

    def test_dump_tokens_verbose(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                with redirect_stdout(io.StringIO()):
                    code = main(["-", "--dump-tokens", "-v"])
        assert code == 0
        assert "tokens=" in err.getvalue()

    def test_dump_ast_verbose(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                with redirect_stdout(io.StringIO()):
                    code = main(["-", "--dump-ast", "-v"])
        assert code == 0
        assert "top_level_nodes=" in err.getvalue()

    def test_mutually_exclusive_modes(self):
        with patch("template_engine.cli._read_template", return_value="x"):
            with pytest.raises(SystemExit):
                main(["-", "--check", "--dump-tokens"])

    def test_template_engine_error_exit(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{"):
            with redirect_stderr(err):
                code = main(["-"])
        assert code == 1

    def test_os_error_exit(self, tmp_path):
        err = io.StringIO()
        missing = tmp_path / "missing.tmpl"
        with redirect_stderr(err):
            code = main([str(missing)])
        assert code == 2

    def test_internal_error_exit(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", side_effect=RuntimeError("boom")):
            with redirect_stderr(err):
                code = main(["-"])
        assert code == 3
        assert "internal error" in err.getvalue()

    def test_strict_mode(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ missing }}"):
            with redirect_stderr(err):
                code = main(["-", "--strict"])
        assert code == 1

    def test_no_autoescape(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--set", "x=<b>", "--no-autoescape"])
        assert code == 0
        assert out.getvalue() == "<b>"

    def test_include_comments_dump(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{# c #}{{ x }}"):
            with redirect_stdout(out):
                code = main(["-", "--dump-tokens", "--include-comments"])
        assert code == 0
        assert "COMMENT" in out.getvalue()

    def test_context_file(self, tmp_context_file):
        path = tmp_context_file({"name": "Ada"})
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ name }}"):
            with redirect_stdout(out):
                code = main(["-", "--context", str(path)])
        assert code == 0
        assert out.getvalue() == "Ada"

    def test_invalid_context_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="x"):
            with redirect_stderr(err):
                code = main(["-", "--context", str(bad)])
        assert code == 2

    def test_filter_module(self):
        out = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x | exclaim }}"):
            with redirect_stdout(out):
                code = main(["-", "--set", "x=hi", "--filter-module", "tests.support.custom_filters"])
        assert code == 0
        assert out.getvalue() == "hi!"

    def test_filter_module_not_found(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                code = main(["-", "--filter-module", "no_such_module_ever"])
        assert code == 2

    def test_invalid_set(self):
        err = io.StringIO()
        with patch("template_engine.cli._read_template", return_value="{{ x }}"):
            with redirect_stderr(err):
                code = main(["-", "--set", "bad"])
        assert code == 2
